import Foundation

struct VideoFile: Identifiable, Hashable, Sendable {
    let id: UUID
    let url: URL
    let fileName: String
    let fileSizeBytes: Int64
    let durationSeconds: Double?

    init(url: URL, fileSizeBytes: Int64, durationSeconds: Double?) {
        self.id = UUID()
        self.url = url
        self.fileName = url.lastPathComponent
        self.fileSizeBytes = fileSizeBytes
        self.durationSeconds = durationSeconds
    }

    var formattedDuration: String {
        guard let durationSeconds, durationSeconds.isFinite, durationSeconds > 0 else {
            return "—"
        }
        let total = Int(durationSeconds.rounded())
        let hours = total / 3600
        let minutes = (total % 3600) / 60
        let seconds = total % 60
        if hours > 0 {
            return String(format: "%d:%02d:%02d", hours, minutes, seconds)
        }
        return String(format: "%d:%02d", minutes, seconds)
    }

    var formattedFileSize: String {
        ByteCountFormatter.string(fromByteCount: fileSizeBytes, countStyle: .file)
    }
}
