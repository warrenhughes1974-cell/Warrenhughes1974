import Foundation

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
            return "Keeps more breathing room before and after detected audio."
        case .balanced:
            return "A natural middle ground for most spoken video."
        case .aggressive:
            return "Cuts closer to detected audio and removes more quiet time."
        }
    }
}
