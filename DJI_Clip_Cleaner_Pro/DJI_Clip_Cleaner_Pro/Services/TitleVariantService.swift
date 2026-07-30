import Foundation

struct TitleVariant: Identifiable, Sendable, Equatable {
    let id: UUID
    let title: String
    let ctrScore: Int
    let reasons: [String]

    init(
        id: UUID = UUID(),
        title: String,
        ctrScore: Int,
        reasons: [String]
    ) {
        self.id = id
        self.title = title
        self.ctrScore = ctrScore
        self.reasons = reasons
    }
}

enum TitleVariantService {
    /// Builds ten distinct title options and sorts them by a CTR-oriented score.
    static func generate(
        hook: String,
        brand: BrandSettingsValues,
        preset: BrandPreset,
        includeChannel: Bool = false
    ) -> [TitleVariant] {
        let cleanHook = normalize(hook)
        let series = brand.seriesName.trimmingCharacters(in: .whitespacesAndNewlines)
        let channel = brand.channelPrefix.trimmingCharacters(in: .whitespacesAndNewlines)

        guard !cleanHook.isEmpty else { return [] }

        var drafts = templates(
            hook: cleanHook,
            series: series,
            preset: preset
        )

        if includeChannel, !channel.isEmpty {
            drafts = drafts.map { draft in
                if draft.localizedCaseInsensitiveContains(channel) {
                    return draft
                }

                let withChannel = "\(draft) | \(channel)"
                return withChannel.count <= YouTubeMetadataService.hardTitleLimit
                    ? withChannel
                    : draft
            }
        }

        var unique: [String] = []
        for draft in drafts {
            let trimmed = draft.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !trimmed.isEmpty else { continue }
            guard !unique.contains(where: { $0.caseInsensitiveCompare(trimmed) == .orderedSame }) else {
                continue
            }
            unique.append(trimmed)
        }

        let scored = unique.map { title in
            let analysis = score(title, hook: cleanHook, series: series, preset: preset)
            return TitleVariant(
                title: title,
                ctrScore: analysis.score,
                reasons: analysis.reasons
            )
        }

        return scored
            .sorted { lhs, rhs in
                if lhs.ctrScore == rhs.ctrScore {
                    return lhs.title.count < rhs.title.count
                }
                return lhs.ctrScore > rhs.ctrScore
            }
            .prefix(10)
            .map { $0 }
    }

    // MARK: - Templates

    private static func templates(
        hook: String,
        series: String,
        preset: BrandPreset
    ) -> [String] {
        let seriesBit = series.isEmpty ? "" : series
        var list: [String] = [
            hook,
            "\(hook)?!",
            "I Found \(hook)",
            "\(hook) Is HERE!",
            "Wait Until You See \(hook)",
            "The BEST \(hook)",
            "\(hook) — Don't Skip This",
            "You Need To See \(hook)",
            "\(hook) Changed Everything"
        ]

        switch preset {
        case .halloweenHunt:
            list += [
                "Halloween Merch is HERE!",
                "\(hook) at the Store Already?!",
                "Spooky Season Find: \(hook)",
                "Code Orange: \(hook)",
                "I Found the BEST Halloween Decor"
            ]
        case .storeWalk:
            list += [
                "Store Walk: \(hook)",
                "What's New: \(hook)",
                "Aisle Find — \(hook)",
                "I Walked In and Found \(hook)"
            ]
        case .productReview:
            list += [
                "\(hook) Review — Worth It?",
                "Honest Take: \(hook)",
                "Don't Buy \(hook) Until You Watch",
                "\(hook) First Look"
            ]
        case .behindTheScenes:
            list += [
                "Behind the Scenes: \(hook)",
                "How I Shot \(hook)",
                "BTS — \(hook)"
            ]
        case .custom:
            list += [
                "New Video: \(hook)",
                "Today's Find: \(hook)"
            ]
        }

        if !seriesBit.isEmpty {
            list += [
                "\(hook) | \(seriesBit)",
                "\(seriesBit): \(hook)",
                "\(hook) — \(seriesBit) Update"
            ]
        }

        return list
    }

    // MARK: - Scoring

    private static func score(
        _ title: String,
        hook: String,
        series: String,
        preset: BrandPreset
    ) -> (score: Int, reasons: [String]) {
        var points = 55
        var reasons: [String] = []
        let count = title.count
        let lower = title.lowercased()

        if count >= 35 && count <= 60 {
            points += 18
            reasons.append("ideal length")
        } else if count >= 28 && count <= 70 {
            points += 10
            reasons.append("good length")
        } else if count < 28 {
            points -= 8
        } else {
            points -= 10
            reasons.append("may truncate")
        }

        let powerWords = [
            "best", "wait", "don't", "need", "here", "already", "secret",
            "worth", "crazy", "insane", "finally", "new", "shocking"
        ]
        if powerWords.contains(where: { lower.contains($0) }) {
            points += 8
            reasons.append("power word")
        }

        if title.contains("?") || title.contains("!") {
            points += 6
            reasons.append("curiosity")
        }

        if title.rangeOfCharacter(from: .decimalDigits) != nil {
            points += 4
            reasons.append("specific")
        }

        if lower.contains(hook.lowercased()) {
            points += 7
            reasons.append("hook first")
        }

        if !series.isEmpty, lower.contains(series.lowercased()) {
            points += 3
            reasons.append("series cue")
        }

        switch preset {
        case .halloweenHunt:
            if lower.contains("halloween") || lower.contains("spooky") || lower.contains("code orange") {
                points += 5
                reasons.append("seasonal")
            }
        case .storeWalk:
            if lower.contains("store") || lower.contains("aisle") || lower.contains("found") {
                points += 4
            }
        case .productReview:
            if lower.contains("review") || lower.contains("worth") {
                points += 4
            }
        case .behindTheScenes:
            if lower.contains("behind") || lower.contains("bts") {
                points += 4
            }
        case .custom:
            break
        }

        // Soft penalty for all-caps shouting whole titles.
        let letters = title.filter(\.isLetter)
        let uppercase = letters.filter(\.isUppercase).count
        if !letters.isEmpty, Double(uppercase) / Double(letters.count) > 0.7, title.count > 12 {
            points -= 6
        }

        return (min(max(points, 1), 99), Array(reasons.prefix(3)))
    }

    private static func normalize(_ value: String) -> String {
        value
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression)
    }
}
