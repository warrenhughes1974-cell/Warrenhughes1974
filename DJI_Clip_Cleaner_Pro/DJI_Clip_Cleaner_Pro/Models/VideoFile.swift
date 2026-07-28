import Foundation

struct VideoFile: Identifiable, Hashable {
    let id = UUID()
    let url: URL
    let duration: TimeInterval
    let fileSize: Int64

    var name: String {
        url.lastPathComponent
    }

    var formattedDuration: String {
        Self.formatDuration(duration)
    }

    var formattedFileSize: String {
        ByteCountFormatter.string(
            fromByteCount: fileSize,
            countStyle: .file
        )
    }

    static func formatDuration(_ duration: TimeInterval) -> String {
        guard duration.isFinite, duration >= 0 else {
            return "0:00"
        }

        let totalSeconds = Int(duration.rounded())
        let hours = totalSeconds / 3600
        let minutes = (totalSeconds % 3600) / 60
        let seconds = totalSeconds % 60

        if hours > 0 {
            return String(
                format: "%d:%02d:%02d",
                hours,
                minutes,
                seconds
            )
        }

        return String(
            format: "%d:%02d",
            minutes,
            seconds
        )
    }
}
