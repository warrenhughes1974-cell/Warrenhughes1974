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

        if let transcript {
            let brief = StoryBriefService.build(
                from: transcript,
                hook: trimmedHook,
                brand: BrandSettings.shared.values
            )
            if !brief.thumbnailText.isEmpty {
                return brief.thumbnailText
            }
        }

        return YouTubeMetadataService.thumbnailText(from: trimmedHook)
    }

    func hookDidChange() {
        guard !hasEditedThumbnailText else { return }
        if let transcript {
            let brief = StoryBriefService.build(
                from: transcript,
                hook: trimmedHook,
                brand: BrandSettings.shared.values
            )
            thumbnailText = brief.thumbnailText.isEmpty
                ? YouTubeMetadataService.thumbnailText(from: trimmedHook)
                : brief.thumbnailText
        } else {
            thumbnailText = YouTubeMetadataService.thumbnailText(from: trimmedHook)
        }
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
        let derived: String
        if let transcript {
            derived = StoryBriefService.build(
                from: transcript,
                hook: trimmedHook,
                brand: BrandSettings.shared.values
            ).thumbnailText
        } else {
            derived = YouTubeMetadataService.thumbnailText(from: trimmedHook)
        }
        hasEditedThumbnailText = !typed.isEmpty
            && typed != derived
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
        thumbnailText = ""
        hasEditedThumbnailText = false
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
                let baseBrand = BrandSettings.shared.values
                let brief = StoryBriefService.build(
                    from: transcript,
                    hook: trimmedHook,
                    brand: baseBrand
                )
                let brand = storyBrand(base: baseBrand, brief: brief)
                let folder = try thumbnailFolder(for: selectedVideoURL)
                let thumbText = resolvedThumbnailText.isEmpty
                    ? brief.thumbnailText
                    : resolvedThumbnailText
                let ranked = try await ThumbnailIntelligenceService.rankFrames(
                    videoURL: selectedVideoURL,
                    thumbnailText: thumbText,
                    brand: brand,
                    outputFolder: folder,
                    storyBrief: brief,
                    progress: { scanned, total in
                        self.thumbnailScanProgress = Double(scanned) / Double(max(total, 1))
                        self.statusMessage = "Scoring frame \(scanned) of \(total)..."
                    }
                )

                rankedThumbnails = ranked
                hasRankedThumbnails = true
                selectedThumbnailID = ranked.first?.id
                thumbnailPath = ranked.first?.imagePath ?? ""
                statusMessage = "Top \(ranked.count) story-matched thumbnails ready — click one to select it."
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
                let baseBrand = BrandSettings.shared.values
                let brief = StoryBriefService.build(
                    from: transcript,
                    hook: trimmedHook,
                    brand: baseBrand
                )
                let brand = storyBrand(base: baseBrand, brief: brief)
                let outputURL = try thumbnailOutputURL(for: selectedVideoURL)

                try await ThumbnailService.generate(
                    from: selectedVideoURL,
                    title: brief.thumbnailText.isEmpty
                        ? resolvedThumbnailText
                        : brief.thumbnailText,
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

                if trimmedHook.isEmpty || isWeakAutomaticHook(trimmedHook) {
                    hook = suggestedHook(from: result)
                }
                // A new transcript is a new source of truth. Replace stale text
                // carried from a previous run; edits made after this remain manual.
                let brief = StoryBriefService.build(
                    from: result,
                    hook: trimmedHook,
                    brand: BrandSettings.shared.values
                )
                hasEditedThumbnailText = false
                thumbnailText = brief.thumbnailText
                refreshTitleVariants()

                statusMessage = "Transcription complete. Generate description and tags to use the story."
            } catch {
                transcript = nil
                errorMessage = error.localizedDescription
                statusMessage = "Transcription failed."
            }

            isTranscribing = false
        }
    }

    private func isWeakAutomaticHook(_ value: String) -> Bool {
        let lower = value.lowercased()
        let weakPhrases = [
            "don't skip this",
            "dont skip this",
            "everything worth seeing",
            "processed update",
            "new video"
        ]
        if weakPhrases.contains(where: { lower.contains($0) }) {
            return true
        }
        let meaningful = lower
            .split(separator: " ")
            .filter { !["american", "airline", "airlines", "video"].contains(String($0)) }
        return meaningful.isEmpty
    }

    private func storyBrand(
        base: BrandSettingsValues,
        brief: StoryBrief
    ) -> BrandSettingsValues {
        let color: (red: Double, green: Double, blue: Double)
        switch brief.domain {
        case .travelDelay, .cruise:
            color = (1.0, 1.0, 1.0)
        case .cooking:
            color = (1.0, 0.62, 0.18)
        case .motorsport:
            color = (1.0, 0.22, 0.18)
        case .adventure:
            color = (1.0, 0.86, 0.15)
        case .themePark:
            color = (1.0, 0.38, 0.70)
        case .family, .general:
            color = (1.0, 1.0, 1.0)
        case .retailHunt:
            color = (
                base.titlePinkRed,
                base.titlePinkGreen,
                base.titlePinkBlue
            )
        }

        return BrandSettingsValues(
            channelPrefix: base.channelPrefix,
            seriesName: base.seriesName,
            defaultHook: base.defaultHook,
            titleFormat: base.titleFormat,
            usePinkTitles: true,
            titlePinkRed: color.red,
            titlePinkGreen: color.green,
            titlePinkBlue: color.blue,
            titleScale: min(base.titleScale, 1.0),
            thumbnailEmojis: (brief.domain == .retailHunt && brief.seriesFits)
                ? base.thumbnailEmojis
                : [],
            emojiPosition: base.emojiPosition
        )
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
        YouTubeMetadataService.storyHookSuggestion(
            from: transcript,
            fallbackURL: selectedVideoURL,
            fallbackSeries: BrandSettings.shared.seriesName,
            brand: BrandSettings.shared.values
        )
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
