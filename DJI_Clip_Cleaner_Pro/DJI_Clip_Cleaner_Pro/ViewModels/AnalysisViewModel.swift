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

    private var analysisTask: Task<Void, Never>?

    func chooseFolder() {
        guard !isScanning, !isAnalyzing else { return }

        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.prompt = "Analyze Folder"
        panel.message = "Select a folder containing video clips."

        guard panel.runModal() == .OK, let url = panel.url else { return }
        selectedFolderURL = url
        Task { await scanFolder(url) }
    }

    func scanFolder(_ folderURL: URL) async {
        analysisTask?.cancel()

        isScanning = true
        isAnalyzing = false
        errorMessage = nil
        results = []
        statusMessage = "Scanning folder..."

        do {
            let urls = try FolderScanner.scanVideos(in: folderURL)
            guard !urls.isEmpty else {
                statusMessage = "No supported video files found in this folder."
                isScanning = false
                return
            }

            statusMessage = "Loading metadata for \(urls.count) clip(s)..."
            let videos = await VideoMetadataService.loadVideoFiles(from: urls)
            results = videos.map { AnalysisResult(video: $0) }
            isScanning = false

            await runAnalysis()
        } catch {
            errorMessage = error.localizedDescription
            statusMessage = "Scan failed."
            isScanning = false
        }
    }

    func rescan() {
        guard let selectedFolderURL else { return }
        Task { await scanFolder(selectedFolderURL) }
    }

    func cancelAnalysis() {
        analysisTask?.cancel()
        isAnalyzing = false
        statusMessage = "Analysis cancelled."
    }

    private func runAnalysis() async {
        guard !results.isEmpty else { return }

        isAnalyzing = true
        statusMessage = "Analyzing \(results.count) clip(s)..."

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
                    motion: motionResult
                )
                results[index].recommendation = recommendation.0
                results[index].notes = recommendation.1
            }

            if Task.isCancelled {
                statusMessage = "Analysis cancelled."
            } else {
                statusMessage = "Analysis complete for \(results.count) clip(s)."
            }

            isAnalyzing = false
        }

        await analysisTask?.value
    }
}

#if canImport(AppKit)
import AppKit
#endif
