import Foundation
import Observation
import UniformTypeIdentifiers

#if canImport(AppKit)
import AppKit
#endif

@MainActor
@Observable
final class YouTubePrepViewModel {
    var selectedVideoURL: URL?
    var hook = ""
    var thumbnailText = ""
    var placesText = ""
    var includeChannelInTitle = false
    var transcript: Transcript?
    var isTranscribing = false
    var titleVariants: [TitleVariant] = []
    var selectedTitleID: UUID?
    var rankedThumbnails: [RankedThumbnailCandidate] = []
    var selectedThumbnailID: UUID?
    var isRankingThumbnails = false
    var thumbnailScanProgress: Double = 0
    var hasRankedThumbnails = false
    var generatedDescription = ""
    var generatedTags: [String] = []
    var thumbnailPath = ""
    var statusMessage = "Choose your finished Filmora video to start YouTube prep."
    var errorMessage: String?
    var isWorking = false

    private var hasEditedThumbnailText = false

    private static let lastVideoPathKey = "youtubePrepLastVideoPath"

    init() {
        restoreLastVideoIfAvailable()
    }

    var trimmedHook: String {
        hook.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// Stores the user typed in. Speech recognition misses a lot of brand names,
    /// so this is the reliable way to get them into the description and tags.
    var manualPlaces: [String] {
        placesText
            .split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }

    var detectedPlacesSummary: String {
        let detected = TranscriptKeywordService.places(from: transcript)

        guard !detected.isEmpty else {
            return transcript == nil
                ? "Transcribe first. Known store names you said out loud are picked up automatically."
                : "No known store names were recognized. Type them above — cities and misheard words are never treated as stores."
        }

        return "Heard in the video: \(detected.joined(separator: ", "))"
    }

    var canGenerate: Bool {
        selectedVideoURL != nil && !trimmedHook.isEmpty && !isTranscribing && !isRankingThumbnails
    }

    var canTranscribe: Bool {
        selectedVideoURL != nil && !isWorking && !isTranscribing && !isRankingThumbnails
    }

    var canRankThumbnails: Bool {
        selectedVideoURL != nil &&
        !resolvedThumbnailText.isEmpty &&
        !isWorking &&
        !isTranscribing &&
        !isRankingThumbnails
    }

    var transcriptSummary: String {
        guard let transcript else {
            return "No transcript yet. Transcribe once to unlock real chapters, better tags, and spoken-word descriptions."
        }

        let words = transcript.fullText.split(separator: " ").count
        let mode = transcript.usedOnDevice ? "on-device" : "network"
        return "Transcript ready · \(words) words · \(transcript.segments.count) timed words · \(mode)"
    }

    var generatedTitle: String {
        if let selectedTitleID,
           let selected = titleVariants.first(where: { $0.id == selectedTitleID }) {
            return selected.title
        }

        return YouTubeMetadataService.buildTitle(
            hook: trimmedHook,
            brand: BrandSettings.shared.values,
            includeChannel: includeChannelInTitle
        )
    }

    var selectedRankedThumbnail: RankedThumbnailCandidate? {
        guard let selectedThumbnailID else {
            return rankedThumbnails.first
        }

        return rankedThumbnails.first(where: { $0.id == selectedThumbnailID }) ?? rankedThumbnails.first
    }

    var titleQuality: MetadataQuality {
        YouTubeMetadataService.titleQuality(generatedTitle)
    }

    var thumbnailTextQuality: MetadataQuality {
        YouTubeMetadataService.thumbnailTextQuality(resolvedThumbnailText)
    }

    var descriptionQuality: MetadataQuality {
        YouTubeMetadataService.descriptionQuality(generatedDescription)
    }

    var tagsQuality: MetadataQuality {
        YouTubeMetadataService.tagsQuality(generatedTags)
    }

    var tagsLine: String {
        generatedTags.joined(separator: ", ")
    }

    var resolvedThumbnailText: String {
        let typed = thumbnailText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard typed.isEmpty else { return typed }

        return YouTubeMetadataService.thumbnailText(from: trimmedHook)
    }

    func hookDidChange() {
        guard !hasEditedThumbnailText else { return }
        thumbnailText = YouTubeMetadataService.thumbnailText(from: trimmedHook)
        refreshTitleVariants()
    }

    func refreshTitleVariants() {
        guard !trimmedHook.isEmpty else {
            titleVariants = []
            selectedTitleID = nil
            return
        }

        titleVariants = TitleVariantService.generate(
            hook: trimmedHook,
            brand: BrandSettings.shared.values,
            preset: BrandSettings.shared.selectedPreset,
            includeChannel: includeChannelInTitle
        )
        selectedTitleID = titleVariants.first?.id
    }

    func selectTitle(_ variant: TitleVariant) {
        selectedTitleID = variant.id
        statusMessage = "Selected title (\(variant.ctrScore) CTR score)."
    }

    func selectThumbnail(_ candidate: RankedThumbnailCandidate) {
        selectedThumbnailID = candidate.id
        thumbnailPath = candidate.imagePath
        statusMessage = "Selected \(candidate.rankLabel.lowercased()) (\(candidate.score))."
    }

    /// `.onChange` also fires for the programmatic write in `hookDidChange()`,
    /// so a value that still matches the derived text does not count as edited.
    func thumbnailTextDidChange() {
        let typed = thumbnailText.trimmingCharacters(in: .whitespacesAndNewlines)
        hasEditedThumbnailText = !typed.isEmpty
            && typed != YouTubeMetadataService.thumbnailText(from: trimmedHook)
    }

    func chooseVideo() {
        #if canImport(AppKit)
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.prompt = "Choose Video"
        panel.message = "Select your finished export from Filmora."
        panel.allowedContentTypes = [.mpeg4Movie, .quickTimeMovie, .movie]

        if let selectedVideoURL {
            panel.directoryURL = selectedVideoURL.deletingLastPathComponent()
        } else if let lastPath = UserDefaults.standard.string(forKey: Self.lastVideoPathKey) {
            panel.directoryURL = URL(fileURLWithPath: lastPath).deletingLastPathComponent()
        }

        guard panel.runModal() == .OK, let url = panel.url else { return }

        selectedVideoURL = url
        UserDefaults.standard.set(url.path, forKey: Self.lastVideoPathKey)
        errorMessage = nil
        thumbnailPath = ""
        transcript = nil
        rankedThumbnails = []
        hasRankedThumbnails = false
        selectedThumbnailID = nil
        titleVariants = []
        selectedTitleID = nil

        if trimmedHook.isEmpty {
            hook = YouTubeMetadataService.hookSuggestion(
                from: url,
                fallbackSeries: BrandSettings.shared.seriesName
            )
            hookDidChange()
        }

        statusMessage = "Ready to prep \(url.lastPathComponent) for YouTube."
        #endif
    }

    func rankThumbnailOptions() {
        guard let selectedVideoURL, canRankThumbnails else {
            errorMessage = "Choose a video and add thumbnail text first."
            return
        }

        isRankingThumbnails = true
        errorMessage = nil
        rankedThumbnails = []
        selectedThumbnailID = nil
        thumbnailScanProgress = 0
        statusMessage = "Scoring about 30 frames for the strongest thumbnails..."

        Task {
            do {
                let brand = BrandSettings.shared.values
                let folder = try thumbnailFolder(for: selectedVideoURL)
                let ranked = try await ThumbnailIntelligenceService.rankFrames(
                    videoURL: selectedVideoURL,
                    thumbnailText: resolvedThumbnailText,
                    brand: brand,
                    outputFolder: folder,
                    progress: { scanned, total in
                        self.thumbnailScanProgress = Double(scanned) / Double(max(total, 1))
                        self.statusMessage = "Scoring frame \(scanned) of \(total)..."
                    }
                )

                rankedThumbnails = ranked
                hasRankedThumbnails = true
                selectedThumbnailID = ranked.first?.id
                thumbnailPath = ranked.first?.imagePath ?? ""
                statusMessage = "Top \(ranked.count) thumbnail pictures ready — click one to select it."
                // Deliberately no Finder reveal here. This is an in-app picker,
                // and activating Finder would cover the results the user is
                // meant to choose from.
            } catch {
                errorMessage = error.localizedDescription
                statusMessage = "Thumbnail ranking failed."
            }

            thumbnailScanProgress = 0
            isRankingThumbnails = false
        }
    }

    func generateThumbnail() {
        guard let selectedVideoURL, canGenerate else {
            errorMessage = "Choose a video and type a hook first."
            return
        }

        // If the user already ranked frames, keep their chosen winner.
        if let selected = selectedRankedThumbnail {
            thumbnailPath = selected.imagePath
            statusMessage = "Using \(selected.rankLabel.lowercased()) (\(selected.score))."
            #if canImport(AppKit)
            NSWorkspace.shared.activateFileViewerSelecting(
                [URL(fileURLWithPath: selected.imagePath)]
            )
            #endif
            return
        }

        isWorking = true
        errorMessage = nil
        statusMessage = "Generating thumbnail..."

        Task {
            do {
                let brand = BrandSettings.shared.values
                let outputURL = try thumbnailOutputURL(for: selectedVideoURL)

                try await ThumbnailService.generate(
                    from: selectedVideoURL,
                    title: resolvedThumbnailText,
                    brand: brand,
                    outputURL: outputURL
                )

                thumbnailPath = outputURL.path
                statusMessage = "Thumbnail saved to \(outputURL.lastPathComponent)"
                #if canImport(AppKit)
                NSWorkspace.shared.activateFileViewerSelecting([outputURL])
                #endif
            } catch {
                errorMessage = error.localizedDescription
                statusMessage = "Thumbnail generation failed."
            }

            isWorking = false
        }
    }

    func transcribeVideo() {
        guard let selectedVideoURL, canTranscribe else {
            errorMessage = "Choose a video first."
            return
        }

        isTranscribing = true
        errorMessage = nil
        statusMessage = "Transcribing speech. Longer videos take a few minutes..."

        Task {
            do {
                let result = try await TranscriptionService.transcribe(videoURL: selectedVideoURL)
                transcript = result

                if trimmedHook.isEmpty {
                    hook = suggestedHook(from: result)
                    hookDidChange()
                }

                statusMessage = "Transcription complete. Generate description and tags to use it."
            } catch {
                transcript = nil
                errorMessage = error.localizedDescription
                statusMessage = "Transcription failed."
            }

            isTranscribing = false
        }
    }

    func generateDescription() {
        guard canGenerate else {
            errorMessage = "Choose a video and type a hook first."
            return
        }

        generatedDescription = YouTubeMetadataService.generateDescription(
            hook: trimmedHook,
            brand: BrandSettings.shared.values,
            preset: BrandSettings.shared.selectedPreset,
            transcript: transcript,
            extraPlaces: manualPlaces
        )
        errorMessage = nil
        statusMessage = transcript == nil
            ? "Description ready. Transcribe first for real chapters from your speech."
            : "Description ready with chapters pulled from your speech."
    }

    func generateTags() {
        guard canGenerate else {
            errorMessage = "Choose a video and type a hook first."
            return
        }

        generatedTags = YouTubeMetadataService.generateTags(
            hook: trimmedHook,
            brand: BrandSettings.shared.values,
            preset: BrandSettings.shared.selectedPreset,
            transcript: transcript,
            extraPlaces: manualPlaces
        )
        errorMessage = nil
        statusMessage = transcript == nil
            ? "Tags ready. Transcribe first to pull phrases you actually said."
            : "Tags ready, including phrases from your transcript."
    }

    private func suggestedHook(from transcript: Transcript) -> String {
        let words = transcript.fullText
            .split(separator: " ")
            .prefix(8)
            .joined(separator: " ")

        return words.isEmpty
            ? YouTubeMetadataService.hookSuggestion(
                from: selectedVideoURL ?? URL(fileURLWithPath: "/"),
                fallbackSeries: BrandSettings.shared.seriesName
            )
            : words
    }

    func generateUploadPackage() {
        guard let selectedVideoURL, canGenerate else {
            errorMessage = "Choose a video and type a hook first."
            return
        }

        if generatedDescription.isEmpty {
            generateDescription()
        }

        if generatedTags.isEmpty {
            generateTags()
        }

        isWorking = true
        errorMessage = nil
        statusMessage = "Building YouTube upload package..."

        Task {
            do {
                let brand = BrandSettings.shared.values

                if thumbnailPath.isEmpty {
                    if let selected = selectedRankedThumbnail {
                        thumbnailPath = selected.imagePath
                    } else {
                        let outputURL = try thumbnailOutputURL(for: selectedVideoURL)
                        try await ThumbnailService.generate(
                            from: selectedVideoURL,
                            title: resolvedThumbnailText,
                            brand: brand,
                            outputURL: outputURL,
                            at: nil
                        )
                        thumbnailPath = outputURL.path
                    }
                }

                let metadata = YouTubeMetadata(
                    title: generatedTitle,
                    thumbnailText: resolvedThumbnailText,
                    description: generatedDescription,
                    tags: generatedTags
                )

                let packageFolder = try YouTubeMetadataService.writeUploadPackage(
                    videoURL: selectedVideoURL,
                    metadata: metadata,
                    thumbnailURL: URL(fileURLWithPath: thumbnailPath)
                )

                if let transcript {
                    let srtURL = packageFolder.appendingPathComponent(
                        "\(YouTubeMetadataService.packageBaseName(from: metadata.title))_captions.srt"
                    )
                    try TranscriptionService.writeSRT(transcript, to: srtURL)
                }

                statusMessage = "Upload package saved to YouTube_Prep/."
                #if canImport(AppKit)
                NSWorkspace.shared.activateFileViewerSelecting([packageFolder])
                #endif
            } catch {
                errorMessage = error.localizedDescription
                statusMessage = "Could not create upload package."
            }

            isWorking = false
        }
    }

    func copyTitle() {
        copyToPasteboard(generatedTitle, label: "Title")
    }

    func copyDescription() {
        copyToPasteboard(generatedDescription, label: "Description")
    }

    func copyTags() {
        copyToPasteboard(tagsLine, label: "Tags")
    }

    private func copyToPasteboard(_ value: String, label: String) {
        #if canImport(AppKit)
        guard !value.isEmpty else { return }
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(value, forType: .string)
        statusMessage = "\(label) copied to clipboard."
        #endif
    }

    private func thumbnailFolder(for videoURL: URL) throws -> URL {
        let folder = videoURL.deletingLastPathComponent().appendingPathComponent(
            YouTubeMetadataService.uploadFolderName,
            isDirectory: true
        )

        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        return folder
    }

    /// Matches the name the upload package uses so the folder holds exactly one
    /// thumbnail rather than a stale duplicate.
    private func thumbnailOutputURL(for videoURL: URL) throws -> URL {
        try thumbnailFolder(for: videoURL).appendingPathComponent(
            YouTubeMetadataService.thumbnailFilename(for: generatedTitle)
        )
    }

    private func restoreLastVideoIfAvailable() {
        guard let path = UserDefaults.standard.string(forKey: Self.lastVideoPathKey) else {
            return
        }

        guard FileManager.default.fileExists(atPath: path) else {
            return
        }

        selectedVideoURL = URL(fileURLWithPath: path)
        statusMessage = "Ready to prep \(URL(fileURLWithPath: path).lastPathComponent) again."
    }
}
