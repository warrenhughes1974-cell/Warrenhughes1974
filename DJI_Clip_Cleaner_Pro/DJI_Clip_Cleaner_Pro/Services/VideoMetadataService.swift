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
            return VideoFile.sortByCaptureDate(results)
        }
    }

    private static func loadVideoFile(from url: URL) async -> VideoFile? {
        let fileSize = (try? url.resourceValues(forKeys: [.fileSizeKey]).fileSize).map(Int64.init) ?? 0
        let asset = AVURLAsset(url: url)

        do {
            let loadedDuration = try await asset.load(.duration)
            let duration = CMTimeGetSeconds(loadedDuration)
            guard duration.isFinite, duration > 0 else {
                return nil
            }
            return VideoFile(url: url, duration: duration, fileSize: fileSize)
        } catch {
            return nil
        }
    }
}
