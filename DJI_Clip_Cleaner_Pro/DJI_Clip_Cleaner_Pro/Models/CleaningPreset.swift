import Foundation

enum CleaningTrimMode: String, CaseIterable, Identifiable {
    case fullClip = "Full Clip"
    case edgesOnly = "Start & End Only"

    var id: String {
        rawValue
    }

    var explanation: String {
        switch self {
        case .fullClip:
            return "Trims silence throughout the entire clip, including pauses between sentences."
        case .edgesOnly:
            return "Trims dead air before you start talking and after you stop. Keeps natural pauses in the middle."
        }
    }
}

enum CleaningPreset: String, CaseIterable, Identifiable {
    case conservative = "Conservative"
    case balanced = "Balanced"
    case aggressive = "Aggressive"

    var id: String {
        rawValue
    }

    var marginSeconds: Double {
        switch self {
        case .conservative:
            return 1.00
        case .balanced:
            return 0.50
        case .aggressive:
            return 0.25
        }
    }

    var explanation: String {
        switch self {
        case .conservative:
            return "Keeps more breathing room at the start and end of each clip."
        case .balanced:
            return "A natural middle ground for trimming clip edges."
        case .aggressive:
            return "Cuts dead air tight at the start and end of each clip."
        }
    }
}
