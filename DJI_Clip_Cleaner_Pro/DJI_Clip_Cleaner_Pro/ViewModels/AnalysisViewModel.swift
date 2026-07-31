import Foundation
import Observation

#if canImport(AppKit)
import AppKit
#endif

@MainActor
@Observable
final class AnalysisViewModel {
    var selectedFolderURL: URL?
    var results: [AnalysisResult] = []
    var isScanning = false
    var isAnalyzing = false
    var statusMessage = "Choose a folder of DJI clips to analyze."
    var errorMessage: String?

    private var scanTask: Task<Void, Never>?
    private var analysisTask: Task<Void, Never>?

    private static let lastFolderPathKey = "analysisLastFolderPath"

    init() {
        restoreLastFolderIfAvailable()
    }

    func chooseFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.prompt = "Analyze Folder"
        panel.message = "Select a folder containing video clips."

        if let selectedFolderURL {
            panel.directoryURL = selectedFolderURL
        } else if let lastPath = UserDefaults.standard.string(forKey: Self.lastFolderPathKey) {
            panel.directoryURL = URL(fileURLWithPath: lastPath)
        }

        guard panel.runModal() == .OK, let url = panel.url else { return }
        rememberFolder(url)
        startScan(for: url)
    }

    func rescan() {
        if let selectedFolderURL {
            startScan(for: selectedFolderURL)
        } else {
            chooseFolder()
        }
    }

    private func rememberFolder(_ url: URL) {
        selectedFolderURL = url
        UserDefaults.standard.set(url.path, forKey: Self.lastFolderPathKey)

        let folderName = url.lastPathComponent

        if let preset = BrandPreset.suggested(from: folderName) {
            BrandSettings.shared.applyPreset(preset)
        } else {
            BrandSettings.shared.seriesName = TitleSuggestionService.suggestedSeriesName(
                from: folderName
            )
            BrandSettings.shared.selectedPreset = .custom
            BrandSettings.shared.save()
        }
    }

    func updateSuggestedHook(for id: UUID, hook: String) {
        guard let index = results.firstIndex(where: { $0.id == id }) else {
            return
        }

        applyHook(hook, to: index)
    }

    private func applyHook(_ hook: String, to index: Int) {
        let brand = BrandSettings.shared.values
        let folderName = selectedFolderURL?.lastPathComponent
        let trimmedHook = hook.trimmingCharacters(in: .whitespacesAndNewlines)

        results[index].suggestedHook = trimmedHook
        results[index].suggestedTitle = TitleSuggestionService.formatTitle(
            hook: trimmedHook,
            brand: brand,
            folderName: folderName
        )
    }

    func refreshSuggestedTitles() {
        guard !results.isEmpty else {
            errorMessage = "Scan a folder first to refresh titles."
            return
        }

        let brand = BrandSettings.shared.values
        let folderName = selectedFolderURL?.lastPathComponent

        for index in results.indices {
            guard results[index].recommendation != .pending else {
                continue
            }

            let hook = TitleSuggestionService.suggestHook(
                video: results[index].video,
                speechSummary: results[index].speechSummary,
                motionSummary: results[index].motionSummary,
                recommendation: results[index].recommendation,
                notes: results[index].notes,
                brand: brand,
                folderName: folderName
            )

            applyHook(hook, to: index)
        }

        statusMessage = "Refreshed hooks and titles using your current brand settings."
        errorMessage = nil
    }

    private func restoreLastFolderIfAvailable() {
        guard let path = UserDefaults.standard.string(forKey: Self.lastFolderPathKey) else {
            return
        }

        var isDirectory: ObjCBool = false
        guard FileManager.default.fileExists(atPath: path, isDirectory: &isDirectory),
              isDirectory.boolValue else {
            return
        }

        selectedFolderURL = URL(fileURLWithPath: path)
        statusMessage = "Ready to rescan \(URL(fileURLWithPath: path).lastPathComponent)."
    }

    private func startScan(for folderURL: URL) {
        scanTask?.cancel()
        analysisTask?.cancel()
        isAnalyzing = false

        scanTask = Task {
            await scanFolder(folderURL)
        }
    }

    func scanFolder(_ folderURL: URL) async {
        if Task.isCancelled {
            return
        }

        rememberFolder(folderURL)

        isScanning = true
        isAnalyzing = false
        errorMessage = nil
        results = []
        statusMessage = "Scanning folder..."

        do {
            let urls = try FolderScanner.scanVideos(in: folderURL)

            if Task.isCancelled {
                isScanning = false
                return
            }

            guard !urls.isEmpty else {
                statusMessage = "No supported video files found in this folder."
                isScanning = false
                return
            }

            statusMessage = "Loading metadata for \(urls.count) clip(s)..."
            let videos = VideoFile.sortByCaptureDate(
                await VideoMetadataService.loadVideoFiles(from: urls)
            )

            if Task.isCancelled {
                isScanning = false
                return
            }

            results = videos.map { AnalysisResult(video: $0) }
            isScanning = false

            await runAnalysis()
        } catch {
            if Task.isCancelled {
                isScanning = false
                return
            }

            errorMessage = error.localizedDescription
            statusMessage = "Scan failed."
            isScanning = false
        }
    }

    func cancelAnalysis() {
        scanTask?.cancel()
        analysisTask?.cancel()
        isScanning = false
        isAnalyzing = false
        statusMessage = "Analysis cancelled."
    }

    var canExportReport: Bool {
        !results.isEmpty
    }

    var canGenerateThumbnails: Bool {
        !results.isEmpty &&
        !isScanning &&
        !isAnalyzing &&
        results.contains { $0.recommendation != .discard && $0.recommendation != .pending }
    }

    var canRunPipeline: Bool {
        !results.isEmpty &&
        !isScanning &&
        !isAnalyzing &&
        results.allSatisfy { $0.recommendation != .pending }
    }

    var pipelineSummary: String {
        let keep = results.filter { $0.recommendation == .keep }.count
        let review = results.filter { $0.recommendation == .review }.count
        let bRoll = results.filter { $0.recommendation == .bRoll }.count
        let discard = results.filter { $0.recommendation == .discard }.count
        return "KEEP \(keep) · B-ROLL \(bRoll) · REVIEW \(review) · DISCARD \(discard)"
    }

    func prepareRunPipeline() -> Bool {
        guard canRunPipeline else {
            errorMessage = pipelineBlockedMessage()
            return false
        }

        errorMessage = nil
        return true
    }

    private func pipelineBlockedMessage() -> String {
        if isScanning || isAnalyzing {
            return "Wait for the current scan to finish before running the pipeline."
        }

        if results.isEmpty {
            return "Scan a folder first using the blue Scan Folder button."
        }

        if results.contains(where: { $0.recommendation == .pending }) {
            return "Wait for analysis to finish on all clips."
        }

        return "The pipeline is not ready yet."
    }

    func runPipeline(
        cleanerViewModel: CleanerViewModel,
        preset: CleaningPreset,
        trimMode: CleaningTrimMode,
        productionPass: ProductionPassSettings,
        stabilize: Bool,
        switchToCleanerTab: () -> Void
    ) {
        guard canRunPipeline, let selectedFolderURL else {
            errorMessage = "Wait for analysis to finish before running the pipeline."
            return
        }

        errorMessage = nil

        do {
            let outcome = try ClipPipelineService.run(
                results: results,
                in: selectedFolderURL
            )

            let pipeline = outcome.pipeline
            let keepVideos = outcome.keepVideos

            guard !keepVideos.isEmpty else {
                statusMessage =
                    "Pipeline moved \(pipeline.movedToDiscard) clip(s) to _DISCARD, but no KEEP clips were found to clean."
                return
            }

            let summary =
                "Moved \(pipeline.movedToDiscard) DISCARD clip(s) to _DISCARD. " +
                "B-ROLL \(pipeline.bRollCount) left in place. " +
                "REVIEW \(pipeline.reviewCount) left in place. " +
                "Cleaning \(pipeline.keepCount) KEEP clip(s)."

            cleanerViewModel.receivePipelineHandoff(
                folder: selectedFolderURL,
                videos: keepVideos,
                summary: summary
            )

            switchToCleanerTab()
            cleanerViewModel.startProcessing(
                using: preset,
                trimMode: trimMode,
                productionPass: productionPass,
                stabilize: stabilize
            )

            statusMessage = summary
        } catch {
            errorMessage = "Pipeline failed: \(error.localizedDescription)"
        }
    }

    func exportReport() {
        guard !results.isEmpty else {
            errorMessage = "Run an analysis before exporting a report."
            return
        }

        let panel = NSSavePanel()
        panel.title = "Export Smart Analysis Report"
        panel.message = "Save a CSV file you can open in Excel or Numbers."
        panel.prompt = "Export"
        panel.canCreateDirectories = true
        panel.nameFieldStringValue = AnalysisReportExporter.defaultFilename()
        panel.allowedContentTypes = [.commaSeparatedText]

        if let selectedFolderURL {
            panel.directoryURL = selectedFolderURL
        }

        guard panel.runModal() == .OK, let url = panel.url else {
            return
        }

        do {
            try AnalysisReportExporter.write(results: results, to: url)
            statusMessage = "Exported \(results.count) clip(s) to \(url.lastPathComponent)"
            NSWorkspace.shared.activateFileViewerSelecting([url])
        } catch {
            errorMessage = "Could not export report: \(error.localizedDescription)"
        }
    }

    func generateThumbnails() {
        guard canGenerateThumbnails, let selectedFolderURL else {
            errorMessage = "Run Smart Analysis first, then generate thumbnails for KEEP, B-ROLL, and REVIEW clips."
            return
        }

        errorMessage = nil

        Task {
            let thumbnailFolder = selectedFolderURL.appendingPathComponent(
                ThumbnailService.outputFolderName,
                isDirectory: true
            )

            do {
                try FileManager.default.createDirectory(
                    at: thumbnailFolder,
                    withIntermediateDirectories: true
                )
            } catch {
                errorMessage = "Could not create Thumbnails folder: \(error.localizedDescription)"
                return
            }

            let brand = BrandSettings.shared.values
            var generated = 0
            var failed = 0

            statusMessage = "Generating branded thumbnails..."

            for index in results.indices {
                let result = results[index]

                guard result.recommendation == .keep
                    || result.recommendation == .review
                    || result.recommendation == .bRoll else {
                    continue
                }

                let baseName = result.video.url
                    .deletingPathExtension()
                    .lastPathComponent

                let outputURL = thumbnailFolder.appendingPathComponent(
                    "\(baseName)_thumb.jpg"
                )

                let title: String
                if !result.suggestedHook.isEmpty {
                    title = TitleSuggestionService.formatTitle(
                        hook: result.suggestedHook,
                        brand: brand,
                        folderName: selectedFolderURL.lastPathComponent
                    )
                } else if !result.suggestedTitle.isEmpty {
                    title = result.suggestedTitle
                } else {
                    title = TitleSuggestionService.suggest(
                        video: result.video,
                        speechSummary: result.speechSummary,
                        motionSummary: result.motionSummary,
                        recommendation: result.recommendation,
                        notes: result.notes,
                        brand: brand,
                        folderName: selectedFolderURL.lastPathComponent
                    )
                }

                do {
                    try await ThumbnailService.generate(
                        from: result.video.url,
                        title: title,
                        brand: brand,
                        outputURL: outputURL
                    )

                    results[index].thumbnailPath = outputURL.path
                    results[index].suggestedTitle = title
                    generated += 1
                } catch {
                    failed += 1
                }
            }

            if generated == 0 {
                statusMessage = "No thumbnails were created."
                errorMessage = failed > 0
                    ? "Thumbnail generation failed for all selected clips."
                    : "No KEEP, B-ROLL, or REVIEW clips were available for thumbnails."
            } else {
                statusMessage = "Created \(generated) branded thumbnail(s) in Thumbnails/."
                if failed > 0 {
                    errorMessage = "\(failed) thumbnail(s) could not be created."
                }
                #if canImport(AppKit)
                NSWorkspace.shared.activateFileViewerSelecting([thumbnailFolder])
                #endif
            }
        }
    }

    private func runAnalysis() async {
        guard !results.isEmpty else { return }

        isAnalyzing = true
        let openAISettings = OpenAISettings.shared
        let cloudAssist = openAISettings.useAIAssistAnalysis && openAISettings.hasAPIKey
        let cloudCutHints = openAISettings.useAICutHints && openAISettings.hasAPIKey
        if cloudAssist && cloudCutHints {
            statusMessage = "Analyzing \(results.count) clip(s) with AI Assist + cut hints…"
        } else if cloudAssist {
            statusMessage = "Analyzing \(results.count) clip(s) with AI Assist…"
        } else if cloudCutHints {
            statusMessage = "Analyzing \(results.count) clip(s) with AI cut hints…"
        } else {
            statusMessage = "Analyzing \(results.count) clip(s)..."
        }
        let settings = AnalysisSettings.shared.values

        analysisTask = Task {
            for index in results.indices {
                if Task.isCancelled { break }

                results[index].speechStatus = .running
                results[index].motionStatus = .running
                results[index].speechSummary = "Detecting..."
                results[index].motionSummary = "Detecting..."
                results[index].cutHints = ""
                statusMessage = "Analyzing \(index + 1) of \(results.count): \(results[index].video.name)"

                let videoURL = results[index].video.url

                async let speech = SpeechAnalyzer.analyze(videoURL: videoURL)
                async let motion = MotionAnalyzer.analyze(videoURL: videoURL)

                let speechResult = await speech
                let motionResult = await motion

                if Task.isCancelled { break }

                results[index].speechStatus = .complete
                results[index].motionStatus = .complete
                results[index].speechSummary = speechResult.summary
                results[index].motionSummary = motionResult.summary

                var recommendation = RecommendationEngine.recommend(
                    video: results[index].video,
                    speech: speechResult,
                    motion: motionResult,
                    settings: settings
                )

                // Optional OpenAI second opinion: demote junk / confirm only.
                let openAI = OpenAISettings.shared
                var clipTranscript: Transcript?

                // Cut hints need a timed transcript; reuse snippet for AI Assist when present.
                if openAI.useAICutHints,
                   openAI.hasAPIKey,
                   let apiKey = openAI.apiKey(),
                   recommendation.0 == .keep
                    || recommendation.0 == .review
                    || recommendation.0 == .bRoll {
                    statusMessage = "Cut-hint transcript \(index + 1) of \(results.count): \(results[index].video.name)"
                    do {
                        if openAI.useWhisper {
                            clipTranscript = try await OpenAIClient.transcribeWithWhisper(
                                videoURL: videoURL,
                                apiKey: apiKey
                            )
                        } else {
                            clipTranscript = try await TranscriptionService.transcribe(
                                videoURL: videoURL
                            )
                        }
                    } catch {
                        // Fall back to on-device if Whisper fails.
                        if openAI.useWhisper {
                            clipTranscript = try? await TranscriptionService.transcribe(
                                videoURL: videoURL
                            )
                        }
                    }
                }

                if openAI.useAIAssistAnalysis,
                   openAI.hasAPIKey,
                   let apiKey = openAI.apiKey(),
                   recommendation.0 != .discard {
                    statusMessage = "AI Assist \(index + 1) of \(results.count): \(results[index].video.name)"
                    do {
                        let assist = try await OpenAIClient.assistClipRecommendation(
                            fileName: results[index].video.name,
                            local: recommendation.0,
                            localNotes: recommendation.1,
                            talkingPercent: speechResult.talkingPercent,
                            motionPercent: motionResult.motionPercent,
                            durationSeconds: results[index].video.duration,
                            jerkSummary: motionResult.jerkSummary,
                            transcriptSnippet: clipTranscript?.fullText,
                            model: openAI.values.model,
                            apiKey: apiKey
                        )
                        recommendation = RecommendationEngine.mergeAIAssist(
                            local: recommendation.0,
                            localNotes: recommendation.1,
                            aiLabel: assist.label,
                            aiReason: assist.reason
                        )
                    } catch {
                        // Fail soft — local recommendation stands.
                    }
                }

                results[index].recommendation = recommendation.0
                results[index].notes = recommendation.1

                if openAI.useAICutHints,
                   openAI.hasAPIKey,
                   let apiKey = openAI.apiKey(),
                   let transcript = clipTranscript,
                   !transcript.isEmpty,
                   recommendation.0 == .keep
                    || recommendation.0 == .review
                    || recommendation.0 == .bRoll {
                    statusMessage = "AI cut hints \(index + 1) of \(results.count): \(results[index].video.name)"
                    do {
                        let hints = try await OpenAIClient.suggestCutHints(
                            fileName: results[index].video.name,
                            recommendation: recommendation.0,
                            durationSeconds: results[index].video.duration,
                            transcript: transcript,
                            model: openAI.values.model,
                            apiKey: apiKey
                        )
                        results[index].cutHints = hints.displayString
                    } catch {
                        // Fail soft — leave cutHints empty.
                    }
                }

                let hook = TitleSuggestionService.suggestHook(
                    video: results[index].video,
                    speechSummary: speechResult.summary,
                    motionSummary: motionResult.summary,
                    recommendation: recommendation.0,
                    notes: recommendation.1,
                    brand: BrandSettings.shared.values,
                    folderName: selectedFolderURL?.lastPathComponent
                )
                applyHook(hook, to: index)
            }

            if Task.isCancelled {
                statusMessage = "Analysis cancelled."
            } else {
                statusMessage = "Analysis complete for \(results.count) clip(s)."
                autoExportReportIfPossible()
            }

            isAnalyzing = false
        }

        await analysisTask?.value
    }

    private func autoExportReportIfPossible() {
        guard let selectedFolderURL else { return }

        let reportURL = selectedFolderURL.appendingPathComponent("Smart_Analysis_Report.csv")

        do {
            try AnalysisReportExporter.write(results: results, to: reportURL)
            statusMessage = "Analysis complete. Report saved to Smart_Analysis_Report.csv"
        } catch {
            statusMessage = "Analysis complete for \(results.count) clip(s). Export failed: \(error.localizedDescription)"
        }
    }
}

// MARK: - Pipeline

struct PipelineResult: Sendable {
    let movedToDiscard: Int
    let skippedDiscard: Int
    let keepCount: Int
    let reviewCount: Int
    let bRollCount: Int
    let discardCount: Int
}

enum ClipPipelineService {
    private static let discardFolderName = "_DISCARD"

    static func run(
        results: [AnalysisResult],
        in folderURL: URL
    ) throws -> (pipeline: PipelineResult, keepVideos: [VideoFile]) {
        let discardFolder = folderURL.appendingPathComponent(
            discardFolderName,
            isDirectory: true
        )

        try FileManager.default.createDirectory(
            at: discardFolder,
            withIntermediateDirectories: true
        )

        var moved = 0
        var skipped = 0
        var keepVideos: [VideoFile] = []
        var reviewCount = 0
        var bRollCount = 0
        var discardCount = 0

        for result in results {
            switch result.recommendation {
            case .discard:
                discardCount += 1
                let source = result.video.url

                guard FileManager.default.fileExists(atPath: source.path) else {
                    skipped += 1
                    continue
                }

                let destination = discardFolder.appendingPathComponent(
                    source.lastPathComponent
                )

                if FileManager.default.fileExists(atPath: destination.path) {
                    skipped += 1
                    continue
                }

                try FileManager.default.moveItem(at: source, to: destination)
                moved += 1

            case .keep:
                keepVideos.append(result.video)

            case .review:
                reviewCount += 1

            case .bRoll:
                bRollCount += 1

            default:
                break
            }
        }

        let pipeline = PipelineResult(
            movedToDiscard: moved,
            skippedDiscard: skipped,
            keepCount: keepVideos.count,
            reviewCount: reviewCount,
            bRollCount: bRollCount,
            discardCount: discardCount
        )

        return (pipeline, VideoFile.sortByCaptureDate(keepVideos))
    }
}

#if canImport(AppKit)
import AppKit
#endif
