import Foundation
import Observation
import UniformTypeIdentifiers

#if canImport(AppKit)
import AppKit
#endif

private enum StoryReviewError: LocalizedError {
    case notConfirmed

    var errorDescription: String? {
        "Review and confirm the story before generating YouTube assets."
    }
}

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
    var storyAnalysis: StoryAnalysis?
    var isAnalyzingStory = false
    var isStoryConfirmed = false
    var storyWarnings: [String] = []
    var storyTitleIdeasText = ""
    var storyThumbnailIdeasText = ""
    var storyVisualTargetsText = ""
    var storyTagsText = ""
    var storyHashtagsText = ""
    var storyChaptersText = ""
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
                ? "Transcribe first. Recognized places will appear in Story Review."
                : "No known places were recognized. Type any missing place above."
        }

        return "Heard in the video: \(detected.joined(separator: ", "))"
    }

    var canGenerate: Bool {
        selectedVideoURL != nil &&
        transcript != nil &&
        isStoryConfirmed &&
        !trimmedHook.isEmpty &&
        !isTranscribing &&
        !isAnalyzingStory &&
        !isRankingThumbnails
    }

    var canTranscribe: Bool {
        selectedVideoURL != nil &&
        !isWorking &&
        !isTranscribing &&
        !isAnalyzingStory &&
        !isRankingThumbnails
    }

    var isBusyForVideoChange: Bool {
        isWorking || isTranscribing || isAnalyzingStory || isRankingThumbnails
    }

    var canRankThumbnails: Bool {
        selectedVideoURL != nil &&
        transcript != nil &&
        isStoryConfirmed &&
        !resolvedThumbnailText.isEmpty &&
        !isWorking &&
        !isTranscribing &&
        !isAnalyzingStory &&
        !isRankingThumbnails
    }

    var transcriptSummary: String {
        guard let transcript else {
            return "No transcript yet. Transcribe once to unlock real chapters, better tags, and spoken-word descriptions."
        }

        let words = transcript.fullText.split(separator: " ").count
        let cloud = OpenAISettings.shared
        let mode = transcript.usedOnDevice
            ? "Apple on-device"
            : (cloud.useWhisper && cloud.hasAPIKey
               ? "\(cloud.provider.displayName) cloud"
               : "Apple network")
        return "Transcript ready · \(words) words · \(transcript.segments.count) timed segments · \(mode)"
    }

    var storyModelStatus: String {
        if isAnalyzingStory {
            return "Apple Intelligence is analyzing the story on this Mac…"
        }
        if let storyAnalysis {
            return "\(storyAnalysis.source.rawValue) · confidence \(storyAnalysis.confidence)%"
        }
        return OnDeviceStoryAnalysisService.availability.message
    }

    var canConfirmStory: Bool {
        guard let storyAnalysis else { return false }
        return !storyAnalysis.subject.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !storyAnalysis.summary.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !parseLines(storyTitleIdeasText).isEmpty
            && !parseLines(storyThumbnailIdeasText).isEmpty
            && !isAnalyzingStory
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

        if let storyAnalysis,
           let first = storyAnalysis.thumbnailTextIdeas.first,
           !first.isEmpty {
            return first
        }

        return YouTubeMetadataService.thumbnailText(from: trimmedHook)
    }

    func hookDidChange() {
        guard !hasEditedThumbnailText else { return }
        if let storyAnalysis,
           let first = storyAnalysis.thumbnailTextIdeas.first,
           !first.isEmpty {
            thumbnailText = first
        } else {
            thumbnailText = YouTubeMetadataService.thumbnailText(from: trimmedHook)
        }
        refreshTitleVariants()
    }

    func refreshTitleVariants() {
        guard isStoryConfirmed, let storyAnalysis else {
            titleVariants = []
            selectedTitleID = nil
            return
        }

        titleVariants = TitleVariantService.generateStoryTitles(
            ideas: storyAnalysis.titleIdeas,
            channel: BrandSettings.shared.channelPrefix,
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
        if let storyAnalysis {
            derived = storyAnalysis.thumbnailTextIdeas.first ?? ""
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
        storyAnalysis = nil
        isStoryConfirmed = false
        storyWarnings = []
        clearStoryEditorText()
        thumbnailText = ""
        hasEditedThumbnailText = false
        rankedThumbnails = []
        hasRankedThumbnails = false
        selectedThumbnailID = nil
        titleVariants = []
        selectedTitleID = nil

        hook = ""

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

        let openAI = OpenAISettings.shared
        let useVision = openAI.useVisionThumbnails && openAI.hasAPIKey
        let providerName = openAI.provider.displayName
        statusMessage = useVision
            ? "Scoring frames, then \(providerName) Vision picks the clickiest thumbnails…"
            : "Scoring about 60 frames for story matches and sharp alternatives..."

        Task {
            do {
                let baseBrand = BrandSettings.shared.values
                guard let brief = reviewedStoryBrief else {
                    throw StoryReviewError.notConfirmed
                }
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
                    storySummary: storyAnalysis?.summary ?? brief.summary,
                    openAIAPIKey: useVision ? openAI.apiKey() : nil,
                    useVisionRerank: useVision,
                    openAIModel: openAI.values.model,
                    cloudProvider: openAI.provider,
                    progress: { scanned, total in
                        self.thumbnailScanProgress = Double(scanned) / Double(max(total, 1))
                        if useVision, scanned >= total {
                            self.statusMessage = "\(providerName) Vision is ranking thumbnail frames…"
                        } else {
                            self.statusMessage = "Scoring frame \(scanned) of \(total)..."
                        }
                    }
                )

                rankedThumbnails = ranked
                hasRankedThumbnails = true
                selectedThumbnailID = ranked.first?.id
                thumbnailPath = ranked.first?.imagePath ?? ""

                if let overlayLine = ranked.first?.reasons.first(where: {
                    $0.hasPrefix("Overlay: ")
                }) {
                    let overlay = String(overlayLine.dropFirst("Overlay: ".count))
                        .trimmingCharacters(in: .whitespacesAndNewlines)
                    if !overlay.isEmpty {
                        thumbnailText = overlay
                        hasEditedThumbnailText = true
                    }
                }

                statusMessage = useVision
                    ? "Top \(ranked.count) Vision-ranked thumbnails ready — punchier frames + AI overlay text."
                    : "Top \(ranked.count) story-matched thumbnails ready — click one to select it."
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
                guard let brief = reviewedStoryBrief else {
                    throw StoryReviewError.notConfirmed
                }
                let brand = storyBrand(base: baseBrand, brief: brief)
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
        let requestedVideoURL = selectedVideoURL

        isTranscribing = true
        errorMessage = nil

        let openAI = OpenAISettings.shared
        let useCloudTranscript = openAI.useWhisper && openAI.hasAPIKey
        statusMessage = useCloudTranscript
            ? "Transcribing with \(openAI.provider.displayName)…"
            : "Transcribing speech. Longer videos take a few minutes..."

        Task {
            do {
                let result: Transcript
                if useCloudTranscript, let apiKey = openAI.apiKey() {
                    do {
                        result = try await CloudAIClient.transcribe(
                            videoURL: requestedVideoURL,
                            provider: openAI.provider,
                            apiKey: apiKey
                        )
                    } catch {
                        // Fall back so a billing/network glitch doesn't block prep.
                        statusMessage = "Cloud transcription failed — falling back to Apple Speech…"
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
                // Spelling-only Channel Context fixes (Brian → Brianna) so Story
                // Review and the visible transcript agree.
                let corrected = OnDeviceStoryAnalysisService.applyingChannelNameCorrections(
                    result,
                    brand: BrandSettings.shared.values
                )
                transcript = corrected
                isTranscribing = false
                await analyzeStory(transcript: corrected)
            } catch {
                transcript = nil
                storyAnalysis = nil
                errorMessage = error.localizedDescription
                statusMessage = "Transcription failed."
            }

            isTranscribing = false
        }
    }

    func reanalyzeStory() {
        guard let transcript else {
            errorMessage = "Transcribe the video first."
            return
        }

        let corrected = OnDeviceStoryAnalysisService.applyingChannelNameCorrections(
            transcript,
            brand: BrandSettings.shared.values
        )
        self.transcript = corrected

        Task {
            await analyzeStory(transcript: corrected)
        }
    }

    private func analyzeStory(transcript: Transcript) async {
        isAnalyzingStory = true
        isStoryConfirmed = false
        errorMessage = nil

        let brand = BrandSettings.shared.values
        let openAI = OpenAISettings.shared
        let useCloud = openAI.useCloudStory && openAI.hasAPIKey

        statusMessage = useCloud
            ? "\(openAI.provider.displayName) is drafting the story…"
            : "Apple Intelligence is analyzing the story on this Mac…"

        if useCloud, let apiKey = openAI.apiKey() {
            do {
                let drafted = try await CloudAIClient.analyzeStory(
                    transcript: transcript,
                    existingHook: trimmedHook,
                    brand: brand,
                    provider: openAI.provider,
                    model: openAI.values.model,
                    apiKey: apiKey
                )
                storyAnalysis = OnDeviceStoryAnalysisService.sanitize(
                    drafted,
                    against: transcript,
                    brand: brand
                )
                // Keep OpenAI attribution even after local sanitize.
                if var analysis = storyAnalysis {
                    analysis.source = .openAI
                    storyAnalysis = analysis
                }
                syncStoryEditorText()
                maybeReplaceBrokenHook()
                statusMessage = "OpenAI story draft ready. Review the facts, then click Confirm Story."
                finishAnalyzeStory()
                return
            } catch {
                statusMessage = "OpenAI story failed — trying on-device analysis…"
                // Fall through to Apple / local path.
            }
        }

        do {
            storyAnalysis = try await OnDeviceStoryAnalysisService.analyze(
                transcript: transcript,
                existingHook: trimmedHook,
                brand: brand
            )
            syncStoryEditorText()
            maybeReplaceBrokenHook()
            statusMessage = "Story analysis ready. Review the facts, then click Confirm Story."
        } catch {
            storyAnalysis = OnDeviceStoryAnalysisService.fallback(
                transcript: transcript,
                hook: trimmedHook,
                brand: brand
            )
            syncStoryEditorText()
            maybeReplaceBrokenHook()
            statusMessage = "\(error.localizedDescription) A local fallback draft is ready; review every field."
        }

        finishAnalyzeStory()
    }

    private func finishAnalyzeStory() {
        storyWarnings = validateStoryAnalysis()
        titleVariants = []
        selectedTitleID = nil
        rankedThumbnails = []
        selectedThumbnailID = nil
        hasRankedThumbnails = false
        isAnalyzingStory = false
    }

    /// Drops garbage hooks left behind by cast scrubbing ("and 's Omaha…").
    private func maybeReplaceBrokenHook() {
        let current = trimmedHook
        let broken = current.lowercased().contains("and 's")
            || current.lowercased().contains("and ’s")
            || current.hasPrefix("and ")
            || current.hasPrefix("'s")
        guard broken, let analysis = storyAnalysis else { return }
        if let title = analysis.titleIdeas.first,
           !title.lowercased().contains("and 's"),
           !title.hasPrefix("and ") {
            hook = title
            return
        }
        if !analysis.subject.isEmpty,
           !analysis.subject.lowercased().contains("and 's"),
           !analysis.subject.hasPrefix("and ") {
            hook = analysis.subject
        }
    }

    func updateStoryText(
        _ keyPath: WritableKeyPath<StoryAnalysis, String>,
        value: String
    ) {
        guard var analysis = storyAnalysis else { return }
        analysis[keyPath: keyPath] = value
        storyAnalysis = analysis
        storyDidChange()
    }

    func updateStoryDomain(_ domain: StoryDomain) {
        guard var analysis = storyAnalysis else { return }
        analysis.domain = domain
        storyAnalysis = analysis
        storyDidChange()
    }

    func storyEditorDidChange() {
        storyDidChange()
    }

    func confirmStoryReview() {
        guard canConfirmStory, var analysis = storyAnalysis else {
            errorMessage = "Add a subject, summary, title idea, and thumbnail text before confirming."
            return
        }

        analysis.titleIdeas = parseLines(storyTitleIdeasText)
        analysis.thumbnailTextIdeas = parseLines(storyThumbnailIdeasText)
        analysis.visualTargets = parseLines(storyVisualTargetsText)
        analysis.tags = parseLines(storyTagsText)
        analysis.hashtags = parseLines(storyHashtagsText)
            .map { $0.hasPrefix("#") ? $0 : "#\($0)" }
            .prefix(3)
            .map { $0 }
        analysis.chapters = parseChapters(storyChaptersText)

        if analysis.domain == .travelDelay,
           !analysis.problemLocation.isEmpty,
           analysis.problemLocation.caseInsensitiveCompare(analysis.destination) == .orderedSame {
            errorMessage = "Problem location and destination are the same. Correct them before confirming."
            return
        }

        analysis.titleIdeas = cleanCompletePhrases(analysis.titleIdeas)
            .filter { $0.count <= YouTubeMetadataService.hardTitleLimit }
        analysis.thumbnailTextIdeas = analysis.thumbnailTextIdeas
            .map { $0.uppercased() }
            .filter { (2...4).contains($0.split(separator: " ").count) }
        analysis.tags = cleanCompletePhrases(analysis.tags)
        storyAnalysis = analysis
        storyWarnings = validateStoryAnalysis()

        guard let firstTitle = analysis.titleIdeas.first,
              let firstThumbnail = analysis.thumbnailTextIdeas.first else {
            errorMessage = "Add at least one complete title and one 2–4 word thumbnail idea."
            return
        }

        hook = firstTitle
        hasEditedThumbnailText = false
        thumbnailText = firstThumbnail
        isStoryConfirmed = true
        errorMessage = nil
        refreshTitleVariants()
        statusMessage = "Story confirmed. Titles, metadata, and thumbnails now use these facts."
    }

    private func storyDidChange() {
        isStoryConfirmed = false
        storyWarnings = validateStoryAnalysis()
        titleVariants = []
        selectedTitleID = nil
        generatedDescription = ""
        generatedTags = []
        rankedThumbnails = []
        selectedThumbnailID = nil
        thumbnailPath = ""
        hasRankedThumbnails = false
        statusMessage = "Story changed — review and confirm again."
    }

    private func validateStoryAnalysis() -> [String] {
        guard let analysis = storyAnalysis else { return [] }
        var warnings: [String] = []

        if analysis.confidence < 60 {
            warnings.append("Low confidence: verify every relationship against the transcript.")
        }
        if analysis.evidence.isEmpty {
            warnings.append("No model evidence matched the transcript exactly. Treat every generated relationship as unverified.")
        }
        if analysis.origin.isEmpty && analysis.problemLocation.isEmpty && analysis.destination.isEmpty {
            warnings.append("No place roles were transcript-supported — leave them blank or type only places you can prove.")
        }
        if analysis.summary.localizedCaseInsensitiveContains("tina")
            || analysis.summary.localizedCaseInsensitiveContains("warren and") {
            warnings.append("Double-check the cast — home/support names should not appear as travelers.")
        }
        if analysis.tags.isEmpty {
            warnings.append("Unsupported theme tags were removed. Add tags only from words actually spoken.")
        }
        if analysis.outcome.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            warnings.append("Outcome is unknown — add what ultimately happened.")
        }
        let effectiveChapters = parseChapters(storyChaptersText)
        if effectiveChapters.isEmpty {
            warnings.append("Generated chapter timing failed validation; add real timestamps or leave chapters blank.")
        }
        if analysis.domain == .travelDelay,
           !analysis.problemLocation.isEmpty,
           analysis.problemLocation.caseInsensitiveCompare(analysis.destination) == .orderedSame {
            warnings.append("Problem location and destination cannot be assumed to be the same.")
        }
        if analysis.titleIdeas.contains(where: { hasDanglingConjunction($0) })
            || analysis.tags.contains(where: { hasDanglingConjunction($0) }) {
            warnings.append("A title or tag ends with an incomplete conjunction.")
        }
        return warnings
    }

    private var reviewedStoryBrief: StoryBrief? {
        guard isStoryConfirmed, let analysis = storyAnalysis else { return nil }

        let places = uniqueNonempty([
            analysis.origin,
            analysis.problemLocation,
            analysis.destination
        ] + manualPlaces)
        let beats = uniqueNonempty([
            analysis.goal,
            analysis.obstacle,
            analysis.outcome
        ])
        let chapters = normalizedChapters(analysis.chapters)

        return StoryBrief(
            domain: analysis.domain,
            headline: analysis.titleIdeas.first ?? analysis.subject,
            summary: analysis.summary,
            places: places,
            beats: beats,
            visualTargets: analysis.visualTargets,
            thumbnailText: analysis.thumbnailTextIdeas.first ?? "",
            tags: cleanCompletePhrases(analysis.tags),
            hashtags: analysis.hashtags,
            chapters: chapters,
            seriesFits: false
        )
    }

    private func cleanCompletePhrases(_ values: [String]) -> [String] {
        var result: [String] = []
        for value in values {
            let clean = value.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !clean.isEmpty, !hasDanglingConjunction(clean) else { continue }
            guard !result.contains(where: { $0.caseInsensitiveCompare(clean) == .orderedSame }) else {
                continue
            }
            result.append(clean)
        }
        return result
    }

    private func hasDanglingConjunction(_ value: String) -> Bool {
        guard let last = value.lowercased().split(separator: " ").last else {
            return true
        }
        return ["and", "or", "but", "at", "to", "from", "with"].contains(String(last))
    }

    private func uniqueNonempty(_ values: [String]) -> [String] {
        var output: [String] = []
        for value in values {
            let clean = value.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !clean.isEmpty else { continue }
            guard !output.contains(where: { $0.caseInsensitiveCompare(clean) == .orderedSame }) else {
                continue
            }
            output.append(clean)
        }
        return output
    }

    private func parseTimecode(_ value: String) -> TimeInterval? {
        let parts = value.split(separator: ":").compactMap { Double($0) }
        if parts.count == 2 {
            return (parts[0] * 60) + parts[1]
        }
        if parts.count == 3 {
            return (parts[0] * 3_600) + (parts[1] * 60) + parts[2]
        }
        return nil
    }

    private func syncStoryEditorText() {
        guard let analysis = storyAnalysis else {
            clearStoryEditorText()
            return
        }
        storyTitleIdeasText = analysis.titleIdeas.joined(separator: "\n")
        storyThumbnailIdeasText = analysis.thumbnailTextIdeas.joined(separator: "\n")
        storyVisualTargetsText = analysis.visualTargets.joined(separator: "\n")
        storyTagsText = analysis.tags.joined(separator: "\n")
        storyHashtagsText = analysis.hashtags.joined(separator: "\n")
        storyChaptersText = analysis.chapters
            .sorted { $0.startTime < $1.startTime }
            .map {
                "\(TranscriptChapter.timecode($0.startTime)) \($0.title)"
            }
            .joined(separator: "\n")
    }

    private func clearStoryEditorText() {
        storyTitleIdeasText = ""
        storyThumbnailIdeasText = ""
        storyVisualTargetsText = ""
        storyTagsText = ""
        storyHashtagsText = ""
        storyChaptersText = ""
    }

    private func parseLines(_ value: String) -> [String] {
        value
            .split(separator: "\n")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }

    private func parseChapters(_ value: String) -> [StoryChapterCandidate] {
        value
            .split(separator: "\n")
            .compactMap { line in
                let parts = line.split(separator: " ", maxSplits: 1)
                guard parts.count == 2,
                      let seconds = parseTimecode(String(parts[0])) else {
                    return nil
                }
                return StoryChapterCandidate(
                    startTime: seconds,
                    title: String(parts[1])
                )
            }
    }

    private func normalizedChapters(
        _ candidates: [StoryChapterCandidate]
    ) -> [TranscriptChapter] {
        let ordered = candidates
            .filter { !$0.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
            .sorted { $0.startTime < $1.startTime }

        var result: [TranscriptChapter] = []
        for candidate in ordered {
            let start = result.isEmpty ? 0 : candidate.startTime
            if let previous = result.last, start - previous.startTime < 10 {
                continue
            }
            result.append(
                TranscriptChapter(startTime: start, title: candidate.title)
            )
        }

        if result.count >= 3 {
            return result
        }

        guard let transcript else { return [] }
        return TranscriptionService.chapters(
            from: transcript,
            storyDomain: storyAnalysis?.domain ?? .general
        )
    }

    private func storyBrand(
        base: BrandSettingsValues,
        brief: StoryBrief
    ) -> BrandSettingsValues {
        // Always honor Settings for color, font, outline, size, and emojis.
        // Story domain used to force white/etc. and ignore the user's brand look.
        _ = brief
        return base
    }

    func generateDescription() {
        guard canGenerate else {
            errorMessage = "Transcribe, review, and confirm the story first."
            return
        }

        guard let brief = reviewedStoryBrief, let analysis = storyAnalysis else {
            errorMessage = StoryReviewError.notConfirmed.localizedDescription
            return
        }

        let openAI = OpenAISettings.shared
        if openAI.useCloudCopy, openAI.hasAPIKey, let apiKey = openAI.apiKey() {
            statusMessage = "\(openAI.provider.displayName) is writing the YouTube description…"
            isWorking = true
            Task {
                do {
                    let pack = try await CloudAIClient.generateUploadCopy(
                        analysis: analysis,
                        title: generatedTitle,
                        brand: BrandSettings.shared.values,
                        transcript: transcript,
                        provider: openAI.provider,
                        model: openAI.values.model,
                        apiKey: apiKey
                    )
                    generatedDescription = pack.description
                    if !pack.tags.isEmpty {
                        generatedTags = pack.tags
                    }
                    if !pack.thumbnailText.isEmpty {
                        thumbnailText = pack.thumbnailText
                        hasEditedThumbnailText = true
                    }
                    if !pack.title.isEmpty {
                        hook = pack.title
                        refreshTitleVariants()
                    }
                    errorMessage = nil
                    statusMessage = "\(openAI.provider.displayName) description ready. Edit anything before upload."
                } catch {
                    // Local fallback keeps the user unblocked.
                    generatedDescription = YouTubeMetadataService.generateDescription(
                        hook: trimmedHook,
                        brand: BrandSettings.shared.values,
                        preset: BrandSettings.shared.selectedPreset,
                        transcript: transcript,
                        extraPlaces: manualPlaces,
                        confirmedBrief: brief,
                        confirmedAnalysis: analysis
                    )
                    errorMessage = nil
                    statusMessage = "OpenAI copy failed (\(error.localizedDescription)). Used local description instead."
                }
                isWorking = false
            }
            return
        }

        generatedDescription = YouTubeMetadataService.generateDescription(
            hook: trimmedHook,
            brand: BrandSettings.shared.values,
            preset: BrandSettings.shared.selectedPreset,
            transcript: transcript,
            extraPlaces: manualPlaces,
            confirmedBrief: brief,
            confirmedAnalysis: analysis
        )
        errorMessage = nil
        statusMessage = "Description built from your confirmed Story Review facts."
    }

    func copyChatGPTPack() {
        guard canGenerate, let analysis = storyAnalysis, isStoryConfirmed else {
            errorMessage = "Confirm the story first, then copy the ChatGPT pack."
            return
        }

        let pack = YouTubeMetadataService.chatGPTPack(
            analysis: analysis,
            title: generatedTitle,
            brand: BrandSettings.shared.values,
            transcript: transcript,
            extraPlaces: manualPlaces
        )
        copyToPasteboard(pack, label: "ChatGPT pack")
        errorMessage = nil
    }

    func generateTags() {
        guard canGenerate else {
            errorMessage = "Transcribe, review, and confirm the story first."
            return
        }

        guard let brief = reviewedStoryBrief else {
            errorMessage = StoryReviewError.notConfirmed.localizedDescription
            return
        }

        generatedTags = YouTubeMetadataService.generateTags(
            hook: trimmedHook,
            brand: BrandSettings.shared.values,
            preset: BrandSettings.shared.selectedPreset,
            transcript: transcript,
            extraPlaces: manualPlaces,
            confirmedBrief: brief
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
                let baseBrand = BrandSettings.shared.values
                guard let brief = reviewedStoryBrief else {
                    throw StoryReviewError.notConfirmed
                }
                let brand = storyBrand(base: baseBrand, brief: brief)

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
