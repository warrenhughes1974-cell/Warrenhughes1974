import Foundation

struct VideoFile: Identifiable, Hashable {
    let id = UUID()
    let url: URL
    let duration: TimeInterval
    let fileSize: Int64
    let recordedAt: Date
    let sequenceNumber: Int

    init(
        url: URL,
        duration: TimeInterval,
        fileSize: Int64,
        recordedAt: Date? = nil,
        sequenceNumber: Int? = nil
    ) {
        self.url = url
        self.duration = duration
        self.fileSize = fileSize

        let parsed = Self.parseCaptureInfo(from: url)
        self.recordedAt = recordedAt ?? parsed.date
        self.sequenceNumber = sequenceNumber ?? parsed.sequenceNumber
    }

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

    var formattedRecordedAt: String {
        Self.recordedAtFormatter.string(from: recordedAt)
    }

    static func sortByCaptureDate(_ videos: [VideoFile]) -> [VideoFile] {
        videos.sorted(by: isInCaptureOrder)
    }

    static func isInCaptureOrder(_ lhs: VideoFile, _ rhs: VideoFile) -> Bool {
        if lhs.recordedAt != rhs.recordedAt {
            return lhs.recordedAt < rhs.recordedAt
        }

        if lhs.sequenceNumber != rhs.sequenceNumber {
            return lhs.sequenceNumber < rhs.sequenceNumber
        }

        return lhs.name.localizedStandardCompare(rhs.name) == .orderedAscending
    }

    static func isInCaptureOrder(url lhs: URL, url rhs: URL) -> Bool {
        let left = parseCaptureInfo(from: lhs)
        let right = parseCaptureInfo(from: rhs)

        if left.date != right.date {
            return left.date < right.date
        }

        if left.sequenceNumber != right.sequenceNumber {
            return left.sequenceNumber < right.sequenceNumber
        }

        return lhs.lastPathComponent.localizedStandardCompare(
            rhs.lastPathComponent
        ) == .orderedAscending
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

    private static let recordedAtFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .medium
        return formatter
    }()

    private static let filenameTimestampFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone.current
        formatter.dateFormat = "yyyyMMddHHmmss"
        return formatter
    }()

    private static func parseCaptureInfo(from url: URL) -> (date: Date, sequenceNumber: Int) {
        let filename = url.lastPathComponent
        var date = fileCreationDate(for: url) ?? .distantPast
        var sequence = 0

        if let timestampRange = filename.range(
            of: #"DJI_(\d{14})"#,
            options: .regularExpression
        ) {
            let match = String(filename[timestampRange])
            let digits = match.replacingOccurrences(of: "DJI_", with: "")

            if let parsed = filenameTimestampFormatter.date(from: digits) {
                date = parsed
            }
        }

        if let sequenceRange = filename.range(
            of: #"_(\d{4})_D\."#,
            options: [.regularExpression, .caseInsensitive]
        ) {
            let match = String(filename[sequenceRange])
            let digits = match
                .replacingOccurrences(of: "_", with: "")
                .replacingOccurrences(of: "D.", with: "")
                .replacingOccurrences(of: "d.", with: "")

            sequence = Int(digits) ?? 0
        } else if let fallbackSequence = filename.range(
            of: #"DJI_(\d{4})\."#,
            options: [.regularExpression, .caseInsensitive]
        ) {
            let match = String(filename[fallbackSequence])
            let digits = match
                .replacingOccurrences(of: "DJI_", with: "")
                .replacingOccurrences(of: ".", with: "")

            sequence = Int(digits) ?? 0
        }

        return (date, sequence)
    }

    private static func fileCreationDate(for url: URL) -> Date? {
        let values = try? url.resourceValues(forKeys: [
            .creationDateKey,
            .contentModificationDateKey
        ])

        return values?.creationDate ?? values?.contentModificationDate
    }
}
