import Foundation

enum TitleSuggestionService {
    static let titleSeparator = " · "

    static func suggest(
        video: VideoFile,
        speechSummary: String,
        motionSummary: String,
        recommendation: ClipRecommendation,
        notes: String,
        brand: BrandSettingsValues,
        folderName: String?
    ) -> String {
        let hook = contentHook(
            speechSummary: speechSummary,
            motionSummary: motionSummary,
            recommendation: recommendation,
            notes: notes,
            video: video,
            seriesName: resolvedSeriesName(brand: brand, folderName: folderName)
        )

        return formatTitle(hook: hook, brand: brand, folderName: folderName)
    }

    static func formatTitle(
        hook: String,
        brand: BrandSettingsValues,
        folderName: String? = nil
    ) -> String {
        let prefix = brand.channelPrefix
        let series = resolvedSeriesName(brand: brand, folderName: folderName)
        let trimmedHook = hook.trimmingCharacters(in: .whitespacesAndNewlines)

        switch brand.titleFormat {
        case .full:
            if !prefix.isEmpty, !series.isEmpty {
                return [prefix, series, trimmedHook].joined(separator: titleSeparator)
            }

            if !prefix.isEmpty {
                return [prefix, trimmedHook].joined(separator: titleSeparator)
            }

            if !series.isEmpty {
                return [series, trimmedHook].joined(separator: titleSeparator)
            }

            return trimmedHook

        case .seriesHook:
            if !series.isEmpty {
                return [series, trimmedHook].joined(separator: titleSeparator)
            }

            if !prefix.isEmpty {
                return [prefix, trimmedHook].joined(separator: titleSeparator)
            }

            return trimmedHook

        case .hookOnly:
            return trimmedHook
        }
    }

    private static func resolvedSeriesName(
        brand: BrandSettingsValues,
        folderName: String?
    ) -> String {
        if !brand.seriesName.isEmpty {
            return brand.seriesName
        }

        guard let folderName,
              !folderName.isEmpty else {
            return ""
        }

        return humanizeFolderName(folderName)
    }

    private static func humanizeFolderName(_ name: String) -> String {
        let cleaned = name
            .replacingOccurrences(of: "_", with: " ")
            .replacingOccurrences(of: "-", with: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)

        guard !cleaned.isEmpty else {
            return ""
        }

        return cleaned
            .split(separator: " ")
            .map { word in
                word.prefix(1).uppercased() + word.dropFirst().lowercased()
            }
            .joined(separator: " ")
    }

    private static func contentHook(
        speechSummary: String,
        motionSummary: String,
        recommendation: ClipRecommendation,
        notes: String,
        video: VideoFile,
        seriesName: String
    ) -> String {
        let hasSpeech = speechSummary.contains("Talking")
        let isStatic = motionSummary.hasPrefix("Static")
        let isMoving = motionSummary.contains("Moving")
        let hasJerk = notes.contains("Sudden movement") || motionSummary.contains("Sudden movement")
        let normalizedSeries = seriesName.lowercased()

        if hasJerk {
            return seriesHook(
                for: normalizedSeries,
                defaultHook: "Quick Camera Moment",
                halloween: "Spooky Camera Jerk",
                storeWalk: "Walking Shot Reset",
                productReview: "Quick Camera Moment",
                behindTheScenes: "Behind The Scenes Moment"
            )
        }

        if recommendation == .discard {
            return seriesHook(
                for: normalizedSeries,
                defaultHook: "Behind The Scenes",
                halloween: "Cut Room Floor",
                storeWalk: "Extra Aisle Footage",
                productReview: "Outtake",
                behindTheScenes: "Setup Footage"
            )
        }

        if hasSpeech && isMoving {
            return seriesHook(
                for: normalizedSeries,
                defaultHook: "Store Walk Discovery",
                halloween: "Creepy Aisle Walk",
                storeWalk: "Store Walk Discovery",
                productReview: "In-Store First Look",
                behindTheScenes: "Walking Setup"
            )
        }

        if hasSpeech && isStatic {
            if video.duration >= 45 {
                return seriesHook(
                    for: normalizedSeries,
                    defaultHook: "Deep Dive Review",
                    halloween: "Halloween Deep Dive",
                    storeWalk: "Store Finds Breakdown",
                    productReview: "Deep Dive Review",
                    behindTheScenes: "Talking Head Setup"
                )
            }

            return seriesHook(
                for: normalizedSeries,
                defaultHook: "Honest Product Review",
                halloween: "Spooky Find Review",
                storeWalk: "Shelf Spotlight",
                productReview: "Honest Product Review",
                behindTheScenes: "Creator Check-In"
            )
        }

        if !hasSpeech && isMoving {
            return seriesHook(
                for: normalizedSeries,
                defaultHook: "Creepy Aisle B-Roll",
                halloween: "Creepy Aisle B-Roll",
                storeWalk: "Walking B-Roll",
                productReview: "Product B-Roll",
                behindTheScenes: "Setup B-Roll"
            )
        }

        if hasSpeech {
            return seriesHook(
                for: normalizedSeries,
                defaultHook: "Talking Head Clip",
                halloween: "Halloween Reaction",
                storeWalk: "Store Commentary",
                productReview: "Quick Take",
                behindTheScenes: "Creator Notes"
            )
        }

        return formattedClipLabel(for: video)
    }

    private static func seriesHook(
        for normalizedSeries: String,
        defaultHook: String,
        halloween: String,
        storeWalk: String,
        productReview: String,
        behindTheScenes: String
    ) -> String {
        if normalizedSeries.contains("halloween") {
            return halloween
        }

        if normalizedSeries.contains("store") || normalizedSeries.contains("walk") {
            return storeWalk
        }

        if normalizedSeries.contains("review") || normalizedSeries.contains("product") {
            return productReview
        }

        if normalizedSeries.contains("behind") || normalizedSeries.contains("bts") {
            return behindTheScenes
        }

        return defaultHook
    }

    static func suggestedSeriesName(from folderName: String) -> String {
        humanizeFolderName(folderName)
    }

    private static func formattedClipLabel(for video: VideoFile) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .none

        let dateLabel = formatter.string(from: video.recordedAt)
        return "Clip\(titleSeparator)\(dateLabel)"
    }
}
