import Foundation
import Observation
import UniformTypeIdentifiers

#if canImport(AppKit)
import AppKit
#endif

struct ShortExportResult: Identifiable, Sendable {
    let id: UUID
    let candidate: ShortCandidate
    let outputURL: URL
    let title: String
}

@MainActor
@Observable
final class ShortsViewModel {
    var selectedVideoURL: URL?
    var longFormTitle = ""
    /// What this Short should express — steers local picks and cloud title refine.
    var themeBrief = ""
    var targetLength: ShortsFinderService.TargetLength = .standard
    var transcript: Transcript?
    var burnCaptions = true
    var candidates: [ShortCandidate] = []
    var selectedCandidateIDs: Set<UUID> = []
    var exported: [ShortExportResult] = []
    var statusMessage = "Choose your finished video to find Shorts moments."
    var errorMessage: String?
    var isAnalyzing = false
    var isExporting = false
    var isTranscribing = false

    private static let lastVideoPathKey = "shortsLastVideoPath"

    init() {
        restoreLastVideoIfAvailable()
    }

    var canAnalyze: Bool {
        selectedVideoURL != nil && !isAnalyzing && !isExporting && !isTranscribing
    }

    var canTranscribe: Bool {
        selectedVideoURL != nil && !isAnalyzing && !isExporting && !isTranscribing
    }

    var canExport: Bool {
        !selectedCandidateIDs.isEmpty && !isAnalyzing && !isExporting && !isTranscribing
    }

    var transcriptSummary: String {
        guard let transcript else {
            return "Transcribe first so moments splice from what you said, captions can burn on, and cloud AI (if enabled) can polish titles."
        }

        let words = transcript.fullText.split(separator: " ").count
        let cloudNote: String
        if transcript.usedOnDevice {
            cloudNote = " · Apple Speech"
        } else {
            // Cloud path (OpenAI Whisper or Gemini) sets usedOnDevice = false.
            let provider = OpenAISettings.shared.provider.displayName
            cloudNote = " · \(provider) transcript"
        }
        return "Transcript ready · \(words) words\(cloudNote) · captions \(burnCaptions ? "ON" : "OFF")"
    }

    var ffmpegInstalled: Bool {
        ProductionPassService.ffmpegPath != nil
    }

    var bridgeChecklist: [String] {
        ShortsMetadataService.bridgeChecklist(
            longFormTitle: longFormTitle.isEmpty ? "your long-form video" : longFormTitle
        )
    }

    func isSelected(_ candidate: ShortCandidate) -> Bool {
        selectedCandidateIDs.contains(candidate.id)
    }

    func toggleSelection(_ candidate: ShortCandidate) {
        if selectedCandidateIDs.contains(candidate.id) {
            selectedCandidateIDs.remove(candidate.id)
        } else {
            selectedCandidateIDs.insert(candidate.id)
        }
    }

    func chooseVideo() {
        #if canImport(AppKit)
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.prompt = "Choose Video"
        panel.message = "Select the finished video you want Shorts from."
        panel.allowedContentTypes = [.mpeg4Movie, .quickTimeMovie, .movie]

        if let selectedVideoURL {
            panel.directoryURL = selectedVideoURL.deletingLastPathComponent()
        } else if let lastPath = UserDefaults.standard.string(forKey: Self.lastVideoPathKey) {
            panel.directoryURL = URL(fileURLWithPath: lastPath).deletingLastPathComponent()
        }

        guard panel.runModal() == .OK, let url = panel.url else { return }

        selectedVideoURL = url
        UserDefaults.standard.set(url.path, forKey: Self.lastVideoPathKey)
        candidates = []
        selectedCandidateIDs = []
        exported = []
        transcript = nil
        errorMessage = nil

        if longFormTitle.isEmpty {
            longFormTitle = YouTubeMetadataService.hookSuggestion(
                from: url,
                fallbackSeries: BrandSettings.shared.seriesName
            )
        }

        statusMessage = "Ready to scan \(url.lastPathComponent) for Shorts moments."
        #endif
    }

    func transcribeVideo() {
        guard let selectedVideoURL, canTranscribe else {
            errorMessage = "Choose a finished video first."
            return
        }
        let requestedVideoURL = selectedVideoURL

        isTranscribing = true
        errorMessage = nil

        let openAI = OpenAISettings.shared
        let useCloudTranscript = openAI.useWhisper && openAI.hasAPIKey
        statusMessage = useCloudTranscript
            ? "Transcribing with \(openAI.provider.displayName) for Shorts…"
            : "Transcribing speech for smarter Shorts picks and captions…"

        Task {
            do {
                let result: Transcript
                var cloudFailedReason: String?
                if useCloudTranscript, let apiKey = openAI.apiKey() {
                    do {
                        result = try await CloudAIClient.transcribe(
                            videoURL: requestedVideoURL,
                            provider: openAI.provider,
                            apiKey: apiKey,
                            model: openAI.activeModel
                        )
                    } catch {
                        cloudFailedReason = error.localizedDescription
                        statusMessage = "Gemini transcription failed — falling back to Apple Speech…"
                        result = try await TranscriptionService.transcribe(
                            videoURL: requestedVideoURL
                        )
                    }
                } else {
                    result = try await TranscriptionService.transcribe(
                        videoURL: requestedVideoURL
                    )
                }

                guard self.selectedVideoURL == requestedVideoURL else {
                    isTranscribing = false
                    return
                }

                transcript = OnDeviceStoryAnalysisService.applyingChannelNameCorrections(
                    result,
                    brand: BrandSettings.shared.values
                )
                if let cloudFailedReason {
                    // Keep this visible — Settings being "on" does not mean Gemini transcribed.
                    errorMessage = "Gemini did not transcribe this video (\(cloudFailedReason)). Using Apple Speech instead."
                    statusMessage = "Apple Speech transcript ready. Fix Gemini (model/quota), then Transcribe again for Google Gemini transcript."
                } else if result.usedOnDevice {
                    statusMessage = "Apple Speech transcript ready. Find Moments will now use what you said."
                } else {
                    statusMessage = "Google Gemini transcript ready. Find Moments will now use what you said."
                }
            } catch {
                transcript = nil
                errorMessage = error.localizedDescription
                statusMessage = "Transcription failed. You can still Find Moments without it."
            }

            isTranscribing = false
        }
    }

    func findMoments() {
        guard let selectedVideoURL else {
            errorMessage = "Choose a finished video first."
            return
        }

        isAnalyzing = true
        errorMessage = nil
        candidates = []
        selectedCandidateIDs = []
        statusMessage = transcript == nil
            ? "Need a transcript to splice a real story. Transcribe first, then Find Moments."
            : "Building Short stories by splicing hook + payoff + button..."

        let length = targetLength
        let activeTranscript = transcript
        let brand = BrandSettings.shared.values
        let preset = BrandSettings.shared.selectedPreset
        let longForm = longFormTitle
        let theme = themeBrief
        let openAI = OpenAISettings.shared
        let useCloudRefine = openAI.useCloudShortsRefine && openAI.hasAPIKey && activeTranscript != nil

        Task {
            var found = await ShortsFinderService.findCandidates(
                in: selectedVideoURL,
                targetLength: length,
                transcript: activeTranscript,
                brand: brand,
                preset: preset,
                longFormTitle: longForm,
                themeBrief: theme
            )

            var cloudNote = ""
            if useCloudRefine,
               let apiKey = openAI.apiKey(),
               let activeTranscript,
               !found.isEmpty {
                statusMessage = "\(openAI.provider.displayName) is ranking Shorts using your theme…"
                do {
                    found = try await CloudAIClient.refineShortCandidates(
                        candidates: found,
                        transcript: activeTranscript,
                        longFormTitle: longForm,
                        themeBrief: theme,
                        brand: brand,
                        preset: preset,
                        provider: openAI.provider,
                        model: openAI.activeModel,
                        apiKey: apiKey
                    )
                    cloudNote = theme.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                        ? " Cloud AI reordered titles."
                        : " Cloud AI ranked to your theme."
                } catch {
                    // Local splices still usable — refine is polish only.
                    cloudNote = " (Cloud refine skipped: \(error.localizedDescription))"
                }
            }

            candidates = found
            // Pre-select everything so the common case is one more click.
            selectedCandidateIDs = Set(found.map(\.id))

            if found.isEmpty {
                statusMessage = "No story assemblies found."
                errorMessage = activeTranscript == nil
                    ? "Transcribe Speech first — story splicing needs what you said."
                    : "Try another length, or re-transcribe if speech was thin."
            } else {
                let spliced = found.filter { $0.beats.count >= 2 }.count
                statusMessage = spliced > 0
                    ? "Built \(found.count) Short story(s) — \(spliced) are multi-cut splices.\(cloudNote) Uncheck any you don’t want, then export."
                    : "Found \(found.count) moment(s). Transcribe for real multi-cut story splices.\(cloudNote)"
            }

            isAnalyzing = false
        }
    }

    func exportSelected() {
        guard let selectedVideoURL else {
            errorMessage = "Choose a finished video first."
            return
        }

        guard !isAnalyzing, !isExporting else {
            errorMessage = "Wait for the current scan or export to finish."
            return
        }

        guard !selectedCandidateIDs.isEmpty else {
            errorMessage = "Select at least one moment to export."
            return
        }

        guard ffmpegInstalled else {
            errorMessage = "FFmpeg was not found. Install it with: brew install ffmpeg"
            return
        }

        let chosen = candidates.filter { selectedCandidateIDs.contains($0.id) }
        let brand = BrandSettings.shared.values
        let preset = BrandSettings.shared.selectedPreset
        let longForm = longFormTitle.isEmpty ? "your long-form video" : longFormTitle

        isExporting = true
        errorMessage = nil
        exported = []

        Task {
            var results: [ShortExportResult] = []
            var failures = 0
            var usedSidecarCaptions = false

            for (offset, candidate) in chosen.enumerated() {
                let number = offset + 1
                statusMessage = "Exporting Short \(number) of \(chosen.count)..."

                do {
                    let product = try await ShortsExportService.export(
                        from: selectedVideoURL,
                        candidate: candidate,
                        index: number,
                        transcript: burnCaptions ? transcript : nil
                    )

                    if product.captionsSidecarURL != nil {
                        usedSidecarCaptions = true
                    }

                    results.append(
                        ShortExportResult(
                            id: candidate.id,
                            candidate: candidate,
                            outputURL: product.url,
                            title: candidate.bestTitle.isEmpty
                                ? ShortsMetadataService.title(
                                    hook: longFormTitle,
                                    index: number
                                )
                                : candidate.bestTitle
                        )
                    )
                } catch {
                    failures += 1
                    errorMessage = error.localizedDescription
                }
            }

            exported = results

            if results.isEmpty {
                statusMessage = "No Shorts were exported."
            } else {
                do {
                    try writeNotes(
                        for: results,
                        videoURL: selectedVideoURL,
                        brand: brand,
                        preset: preset,
                        longFormTitle: longForm,
                        themeBrief: themeBrief
                    )
                } catch {
                    errorMessage = "Shorts exported, but the notes file could not be saved: \(error.localizedDescription)"
                }

                var summary = failures > 0
                    ? "Exported \(results.count) Short(s). \(failures) failed."
                    : "Exported \(results.count) Short(s) to the Shorts folder."

                if usedSidecarCaptions {
                    summary += " Captions saved as .srt files (this FFmpeg cannot burn text onto video). For burned-in captions run: brew reinstall ffmpeg"
                }

                statusMessage = summary

                #if canImport(AppKit)
                NSWorkspace.shared.activateFileViewerSelecting(
                    [ShortsExportService.outputFolder(for: selectedVideoURL)]
                )
                #endif
            }

            isExporting = false
        }
    }

    func revealShortsFolder() {
        #if canImport(AppKit)
        guard let selectedVideoURL else { return }
        let folder = ShortsExportService.outputFolder(for: selectedVideoURL)

        guard FileManager.default.fileExists(atPath: folder.path) else {
            errorMessage = "Export some Shorts first."
            return
        }

        NSWorkspace.shared.activateFileViewerSelecting([folder])
        #endif
    }

    private func writeNotes(
        for results: [ShortExportResult],
        videoURL: URL,
        brand: BrandSettingsValues,
        preset: BrandPreset,
        longFormTitle: String,
        themeBrief: String
    ) throws {
        let folder = ShortsExportService.outputFolder(for: videoURL)
        let description = ShortsMetadataService.description(
            longFormTitle: longFormTitle,
            brand: brand,
            preset: preset
        )

        var lines: [String] = [
            "SHORTS UPLOAD NOTES",
            "From: \(videoURL.lastPathComponent)",
            ""
        ]

        let theme = themeBrief.trimmingCharacters(in: .whitespacesAndNewlines)
        if !theme.isEmpty {
            lines.append("SHORT THEME / INTENT")
            lines.append(theme)
            lines.append("")
        }

        lines.append("POST-UPLOAD CHECKLIST")

        for item in ShortsMetadataService.bridgeChecklist(longFormTitle: longFormTitle) {
            lines.append("- \(item)")
        }

        lines.append("")
        lines.append("DESCRIPTION (use for every Short)")
        lines.append(description)
        lines.append("")
        lines.append("CLIPS")

        for result in results {
            lines.append("")
            lines.append(result.outputURL.lastPathComponent)
            lines.append("  Source timecode: \(result.candidate.formattedRange)")
            lines.append("  Duration: \(result.candidate.formattedDuration)")
            lines.append("  Spoken hook: \(result.candidate.hookLine)")
            lines.append("  Projected Hook: \(result.candidate.projectedHook)")
            lines.append("  Projected Retention: \(result.candidate.projectedRetention)")
            lines.append("  Best title: \(result.title)")
            lines.append("  Why it was picked: \(result.candidate.reason)")
            lines.append("  Story: \(result.candidate.storySummary)")
            for beat in result.candidate.beats {
                lines.append(
                    "  \(beat.role.label): \(beat.formattedRange) (\(Int(beat.duration.rounded()))s) — \(beat.quote)"
                )
            }
            lines.append("")
            lines.append(
                ShortsMetadataService.creativeBrief(
                    for: result.candidate,
                    preset: preset
                ).notesBlock
            )
        }

        try lines
            .joined(separator: "\n")
            .write(
                to: folder.appendingPathComponent("Shorts_upload_notes.txt"),
                atomically: true,
                encoding: .utf8
            )
    }

    private func restoreLastVideoIfAvailable() {
        guard let path = UserDefaults.standard.string(forKey: Self.lastVideoPathKey),
              FileManager.default.fileExists(atPath: path) else {
            return
        }

        selectedVideoURL = URL(fileURLWithPath: path)
        statusMessage = "Ready to scan \(URL(fileURLWithPath: path).lastPathComponent) again."
    }
}
