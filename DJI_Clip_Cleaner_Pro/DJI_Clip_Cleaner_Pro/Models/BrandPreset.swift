import Foundation

enum BrandTitleFormat: String, CaseIterable, Identifiable, Sendable {
    case full = "Channel · Series · Hook"
    case seriesHook = "Series · Hook"
    case hookOnly = "Hook only"

    var id: String { rawValue }

    var displayName: String { rawValue }
}

enum BrandPreset: String, CaseIterable, Identifiable, Sendable {
    case halloweenHunt = "Halloween Hunt"
    case storeWalk = "Store Walk"
    case productReview = "Product Review"
    case behindTheScenes = "Behind the Scenes"
    case custom = "Custom"

    var id: String { rawValue }

    var displayName: String { rawValue }

    var seriesName: String {
        switch self {
        case .halloweenHunt:
            return "Halloween Hunt"
        case .storeWalk:
            return "Store Walk"
        case .productReview:
            return "Product Review"
        case .behindTheScenes:
            return "Behind the Scenes"
        case .custom:
            return ""
        }
    }

    var sampleHook: String {
        switch self {
        case .halloweenHunt:
            return "Creepy Aisle Find"
        case .storeWalk:
            return "Store Walk Discovery"
        case .productReview:
            return "Honest Product Review"
        case .behindTheScenes:
            return "Setup & B-Roll"
        case .custom:
            return "Your Clip Hook"
        }
    }

    static func suggested(from folderName: String) -> BrandPreset? {
        let normalized = folderName.lowercased()

        if normalized.contains("halloween") || normalized.contains("spooky") {
            return .halloweenHunt
        }

        if normalized.contains("store") || normalized.contains("walk") || normalized.contains("aisle") {
            return .storeWalk
        }

        if normalized.contains("review") || normalized.contains("product") {
            return .productReview
        }

        if normalized.contains("behind") || normalized.contains("bts") || normalized.contains("setup") {
            return .behindTheScenes
        }

        return nil
    }
}
