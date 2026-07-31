import Foundation

/// A post-production recipe for one Short — story beats, music, and framing.
struct ShortsCreativeBrief: Sendable {
    let storyShape: String
    let beats: [String]
    let musicMood: String
    let musicSearch: [String]
    let musicMixTip: String
    let framingTips: [String]
    let onScreenText: String
    let endingMove: String

    var notesBlock: String {
        var lines: [String] = []
        lines.append("  How to build this Short")
        lines.append("  Story shape: \(storyShape)")
        for beat in beats {
            lines.append("  • \(beat)")
        }
        lines.append("  Music: \(musicMood)")
        lines.append("  Search YouTube Audio Library / Epidemic for: \(musicSearch.joined(separator: ", "))")
        lines.append("  Mix tip: \(musicMixTip)")
        lines.append("  On-screen text idea: \(onScreenText)")
        lines.append("  Ending: \(endingMove)")
        lines.append("  In Filmora / CapCut:")
        for tip in framingTips {
            lines.append("  - \(tip)")
        }
        return lines.joined(separator: "\n")
    }
}

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

    /// Concrete edit recipe so a spliced story becomes a finished Short.
    static func creativeBrief(
        for candidate: ShortCandidate,
        preset: BrandPreset
    ) -> ShortsCreativeBrief {
        let music = musicIdeas(preset: preset)
        let textIdea = candidate.hookLine.isEmpty
            ? onScreenFallback(preset: preset)
            : candidate.hookLine.uppercased()

        var beats: [String] = []
        var cursor: TimeInterval = 0
        for beat in candidate.beats {
            let startCode = ShortCandidate.timecode(cursor)
            let endCode = ShortCandidate.timecode(cursor + beat.duration)
            let spoken = beat.quote.split(separator: " ").prefix(8).joined(separator: " ")
            let spokenBit = spoken.isEmpty ? "picture only" : "“\(spoken)”"
            beats.append(
                "\(startCode)–\(endCode) \(beat.role.label) from long-video \(beat.formattedRange) — \(spokenBit)"
            )
            cursor += beat.duration
        }

        if beats.isEmpty {
            beats = ["Export the clip, then add text + music in Filmora."]
        }

        return ShortsCreativeBrief(
            storyShape: candidate.storySummary.isEmpty
                ? storyShape(preset: preset, duration: candidate.duration)
                : candidate.storySummary,
            beats: beats,
            musicMood: music.mood,
            musicSearch: music.search,
            musicMixTip: music.mixTip,
            framingTips: framingTips(preset: preset, hasSpeech: !candidate.quote.isEmpty)
                + [
                    "Hard cut between beats — no dissolve. Shorts want snap edits.",
                    "Optional: 2–4 frame flash of black between HOOK and PAYOFF for punch."
                ],
            onScreenText: textIdea,
            endingMove: endingMove(preset: preset)
        )
    }

    private static func storyShape(preset: BrandPreset, duration: TimeInterval) -> String {
        let lengthNote = duration <= 25
            ? "Keep it one idea only."
            : "One idea, but you have room for a tiny setup before the payoff."

        return preset.storyShape(lengthNote: lengthNote)
    }

    private static func musicIdeas(preset: BrandPreset) -> (mood: String, search: [String], mixTip: String) {
        preset.musicIdeas
    }

    private static func framingTips(preset: BrandPreset, hasSpeech: Bool) -> [String] {
        var tips = [
            "Start on a 1.2×–1.4× punch-in so the first frame is already close.",
            "Keep the subject in the center third — Shorts are watched one-handed.",
            "Add captions (burned or auto) in the lower-middle, not covering faces.",
            "Cut every pause longer than about half a second."
        ]

        if hasSpeech {
            tips.append("Prefer your spoken line as the on-screen hook instead of inventing new wording.")
        }

        if let tip = preset.framingExtraTip {
            tips.append(tip)
        }

        return tips
    }

    private static func onScreenFallback(preset: BrandPreset) -> String {
        preset.onScreenFallback
    }

    private static func endingMove(preset: BrandPreset) -> String {
        preset.endingMove
    }

    private static func teaser(preset: BrandPreset) -> String {
        preset.teaser
    }

    private static func hashtags(series: String, preset: BrandPreset) -> String {
        var tags = ["#Shorts"]

        if let tag = preset.shortHashtag {
            tags.append(tag)
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
