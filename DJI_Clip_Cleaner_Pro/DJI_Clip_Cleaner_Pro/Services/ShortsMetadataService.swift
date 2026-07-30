import Foundation

enum ShortsMetadataService {
    /// YouTube only counts the first three hashtags, and #Shorts belongs there.
    static func title(hook: String, index: Int) -> String {
        let cleanHook = hook.trimmingCharacters(in: .whitespacesAndNewlines)
        var base = cleanHook.isEmpty ? "Clip \(index)" : cleanHook

        // Several Shorts come from one video, so anything after the first needs
        // a distinct title rather than a duplicate.
        if !cleanHook.isEmpty, index > 1 {
            base += " — Part \(index)"
        }

        return withShortsHashtag(base)
    }

    /// Picks a Short-specific title from the spoken quote when available.
    static func bestTitle(
        quote: String,
        longFormTitle: String,
        brand: BrandSettingsValues,
        preset: BrandPreset
    ) -> String {
        let spoken = quote.trimmingCharacters(in: .whitespacesAndNewlines)
        let fallbackHook = longFormTitle.trimmingCharacters(in: .whitespacesAndNewlines)

        let seed: String
        if spoken.split(separator: " ").count >= 4 {
            seed = spoken
                .split(separator: " ")
                .prefix(9)
                .joined(separator: " ")
        } else if !fallbackHook.isEmpty {
            seed = fallbackHook
        } else {
            seed = brand.seriesName.isEmpty ? "Quick Find" : brand.seriesName
        }

        let variants = TitleVariantService.generate(
            hook: seed,
            brand: brand,
            preset: preset,
            includeChannel: false
        )

        let best = variants.first?.title ?? seed
        return withShortsHashtag(best)
    }

    private static func withShortsHashtag(_ title: String) -> String {
        let suffix = " #Shorts"
        let cleaned = title
            .replacingOccurrences(of: "#Shorts", with: "", options: .caseInsensitive)
            .trimmingCharacters(in: .whitespacesAndNewlines)

        let limit = YouTubeMetadataService.recommendedTitleLimit - suffix.count
        let trimmed = cleaned.count > limit
            ? String(cleaned.prefix(limit - 1)).trimmingCharacters(in: .whitespaces)
            : cleaned

        return trimmed + suffix
    }

    static func description(
        longFormTitle: String,
        brand: BrandSettingsValues,
        preset: BrandPreset
    ) -> String {
        let channel = brand.channelPrefix.trimmingCharacters(in: .whitespacesAndNewlines)
        let channelName = channel.isEmpty ? "the channel" : channel
        let series = brand.seriesName.trimmingCharacters(in: .whitespacesAndNewlines)

        var lines: [String] = []

        lines.append(teaser(preset: preset))
        lines.append("")
        lines.append("Full video: \(longFormTitle)")
        lines.append("Watch the whole thing on \(channelName).")
        lines.append("")
        lines.append(hashtags(series: series, preset: preset))

        return lines.joined(separator: "\n")
    }

    /// The Shorts and long-form algorithms are separate, so a Short only feeds
    /// the main channel if the viewer is actually pointed at it.
    static func bridgeChecklist(longFormTitle: String) -> [String] {
        [
            "Set the Related Video field on the Short to: \(longFormTitle)",
            "Say \"full video on the channel\" in the last 3 seconds.",
            "End on an open loop so the Short does not fully answer the question.",
            "Post 1 to 2 Shorts per week — above roughly 40% of uploads, long-form starts to suffer.",
            "Pin a comment on the Short linking to the long-form video."
        ]
    }

    private static func teaser(preset: BrandPreset) -> String {
        switch preset {
        case .halloweenHunt:
            return "One of the best finds from this Halloween hunt."
        case .storeWalk:
            return "A quick look at what I found walking the aisles."
        case .productReview:
            return "The part of the review everyone asks about."
        case .behindTheScenes:
            return "A quick behind-the-scenes moment."
        case .custom:
            return "A quick moment from the full video."
        }
    }

    private static func hashtags(series: String, preset: BrandPreset) -> String {
        var tags = ["#Shorts"]

        switch preset {
        case .halloweenHunt:
            tags.append("#halloween")
        case .storeWalk:
            tags.append("#shopwithme")
        case .productReview:
            tags.append("#review")
        case .behindTheScenes:
            tags.append("#behindthescenes")
        case .custom:
            break
        }

        let compactSeries = series
            .components(separatedBy: CharacterSet.alphanumerics.inverted)
            .joined()
            .lowercased()

        if !compactSeries.isEmpty, tags.count < 3 {
            tags.append("#\(compactSeries)")
        }

        return tags.prefix(3).joined(separator: " ")
    }
}
