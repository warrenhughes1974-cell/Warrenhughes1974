import Foundation

enum AnalysisStatus: String, Sendable {
    case pending = "Pending"
    case running = "Detecting..."
    case complete = "Complete"
    case failed = "Failed"
}

enum ClipRecommendation: String, Sendable {
    case pending = "Pending"
    case keep = "KEEP"
    case review = "REVIEW"
    case bRoll = "B-ROLL"
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
    /// Suggested KEEP/CUT ranges from optional OpenAI cut hints (display string).
    var cutHints: String
    var suggestedHook: String
    var suggestedTitle: String
    var thumbnailPath: String

    init(video: VideoFile, id: UUID? = nil) {
        self.id = id ?? video.id
        self.video = video
        self.speechStatus = .pending
        self.motionStatus = .pending
        self.speechSummary = "Pending"
        self.motionSummary = "Pending"
        self.recommendation = .pending
        self.notes = ""
        self.cutHints = ""
        self.suggestedHook = ""
        self.suggestedTitle = ""
        self.thumbnailPath = ""
    }

    /// Keep analysis fields when the file is renamed on disk (REVIEW → NEEDS_REVIEW_…).
    func replacingVideo(_ video: VideoFile) -> AnalysisResult {
        var copy = AnalysisResult(video: video, id: id)
        copy.speechStatus = speechStatus
        copy.motionStatus = motionStatus
        copy.speechSummary = speechSummary
        copy.motionSummary = motionSummary
        copy.recommendation = recommendation
        copy.notes = notes
        copy.cutHints = cutHints
        copy.suggestedHook = suggestedHook
        copy.suggestedTitle = suggestedTitle
        copy.thumbnailPath = thumbnailPath
        return copy
    }
}
