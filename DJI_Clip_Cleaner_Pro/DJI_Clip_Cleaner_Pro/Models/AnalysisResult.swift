import Foundation

enum AnalysisStatus: String, Sendable {
    case pending = "Pending"
    case running = "Detecting..."
    case notImplemented = "Not Yet Implemented"
    case complete = "Complete"
    case failed = "Failed"
}

enum ClipRecommendation: String, Sendable {
    case pending = "Pending"
    case keep = "KEEP"
    case review = "REVIEW"
    case discard = "DISCARD"
    case unknown = "—"
}

struct AnalysisResult: Identifiable {
    let id: UUID
    let video: VideoFile
    var speechStatus: AnalysisStatus
    var motionStatus: AnalysisStatus
    var speechSummary: String
    var motionSummary: String
    var recommendation: ClipRecommendation
    var notes: String
    var suggestedTitle: String
    var thumbnailPath: String

    init(video: VideoFile) {
        self.id = video.id
        self.video = video
        self.speechStatus = .pending
        self.motionStatus = .pending
        self.speechSummary = "Pending"
        self.motionSummary = "Pending"
        self.recommendation = .pending
        self.notes = ""
        self.suggestedTitle = ""
        self.thumbnailPath = ""
    }
}
