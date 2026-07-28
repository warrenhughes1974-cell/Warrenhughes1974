import Foundation
import Observation

@MainActor
@Observable
final class AnalysisViewModel {
    var selectedFolderURL: URL?
    var results: [AnalysisResult] = []
    var isScanning = false
    var statusMessage = "Choose a folder of DJI clips to analyze."
    var errorMessage: String?

    func chooseFolder() {
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
        isScanning = true
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
            statusMessage = "Loaded \(videos.count) clip(s). Analysis columns are ready for future detectors."
            markPlaceholders()
        } catch {
            errorMessage = error.localizedDescription
            statusMessage = "Scan failed."
        }

        isScanning = false
    }

    func rescan() {
        guard let selectedFolderURL else { return }
        Task { await scanFolder(selectedFolderURL) }
    }

    private func markPlaceholders() {
        for index in results.indices {
            results[index].speechStatus = .notImplemented
            results[index].motionStatus = .notImplemented
            results[index].recommendation = .pending
            results[index].notes = "Speech and motion detectors will plug in here."
        }
    }
}

#if canImport(AppKit)
import AppKit
#endif
