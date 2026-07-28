import AVFoundation
import Foundation

struct VideoMetadataService {
    static func loadVideoFiles(from urls: [URL]) async -> [VideoFile] {
        await withTaskGroup(of: VideoFile?.self) { group in
            for url in urls {
                group.addTask {
                    await loadVideoFile(from: url)
                }
            }

            var results: [VideoFile] = []
            for await item in group {
                if let item {
                    results.append(item)
                }
            }
            return results.sorted {
                $0.fileName.localizedStandardCompare($1.fileName) == .orderedAscending
            }
        }
    }

    private static func loadVideoFile(from url: URL) async -> VideoFile? {
        let fileSize = (try? url.resourceValues(forKeys: [.fileSizeKey]).fileSize).map(Int64.init) ?? 0
        let asset = AVURLAsset(url: url)
        let duration: Double?

        do {
            let loadedDuration = try await asset.load(.duration)
            let seconds = CMTimeGetSeconds(loadedDuration)
            duration = seconds.isFinite && seconds > 0 ? seconds : nil
        } catch {
            duration = nil
        }

        return VideoFile(url: url, fileSizeBytes: fileSize, durationSeconds: duration)
    }
}
