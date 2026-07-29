import Foundation
import Observation

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

    var canRunPipeline: Bool {
        !results.isEmpty &&
        !isScanning &&
        !isAnalyzing &&
        results.allSatisfy { $0.recommendation != .pending }
    }

    var pipelineSummary: String {
        let keep = results.filter { $0.recommendation == .keep }.count
        let review = results.filter { $0.recommendation == .review }.count
        let discard = results.filter { $0.recommendation == .discard }.count
        return "KEEP \(keep) · REVIEW \(review) · DISCARD \(discard)"
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
                productionPass: productionPass
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

    private func runAnalysis() async {
        guard !results.isEmpty else { return }

        isAnalyzing = true
        statusMessage = "Analyzing \(results.count) clip(s)..."
        let settings = AnalysisSettings.shared.values

        analysisTask = Task {
            for index in results.indices {
                if Task.isCancelled { break }

                results[index].speechStatus = .running
                results[index].motionStatus = .running
                results[index].speechSummary = "Detecting..."
                results[index].motionSummary = "Detecting..."
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

                let recommendation = RecommendationEngine.recommend(
                    video: results[index].video,
                    speech: speechResult,
                    motion: motionResult,
                    settings: settings
                )
                results[index].recommendation = recommendation.0
                results[index].notes = recommendation.1
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

            default:
                break
            }
        }

        let pipeline = PipelineResult(
            movedToDiscard: moved,
            skippedDiscard: skipped,
            keepCount: keepVideos.count,
            reviewCount: reviewCount,
            discardCount: discardCount
        )

        return (pipeline, VideoFile.sortByCaptureDate(keepVideos))
    }
}

#if canImport(AppKit)
import AppKit
#endif
