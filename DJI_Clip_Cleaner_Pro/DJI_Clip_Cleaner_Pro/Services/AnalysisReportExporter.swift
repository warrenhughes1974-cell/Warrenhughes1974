import Foundation
import UniformTypeIdentifiers

enum AnalysisReportExporter {
    static func makeCSV(from results: [AnalysisResult]) -> String {
        var lines = [
            "Clip,Duration,DurationSeconds,FileSize,Speech,Motion,Recommendation,Reason,FilePath"
        ]

        for result in results {
            let row = [
                result.video.name,
                result.video.formattedDuration,
                String(format: "%.2f", result.video.duration),
                result.video.formattedFileSize,
                result.speechSummary,
                result.motionSummary,
                result.recommendation.rawValue,
                result.notes,
                result.video.url.path
            ]
            .map(csvEscape)
            .joined(separator: ",")

            lines.append(row)
        }

        return lines.joined(separator: "\n")
    }

    static func defaultFilename() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd_HHmmss"
        return "Smart_Analysis_Report_\(formatter.string(from: Date())).csv"
    }

    static func write(results: [AnalysisResult], to url: URL) throws {
        let csv = makeCSV(from: results)
        try csv.write(to: url, atomically: true, encoding: .utf8)
    }

    private static func csvEscape(_ value: String) -> String {
        let needsQuotes =
            value.contains(",") ||
            value.contains("\"") ||
            value.contains("\n") ||
            value.contains("\r")

        let escaped = value.replacingOccurrences(of: "\"", with: "\"\"")
        return needsQuotes ? "\"\(escaped)\"" : escaped
    }
}

extension UTType {
    static let commaSeparatedText = UTType(filenameExtension: "csv") ?? .plainText
}
