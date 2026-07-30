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

    /// Concrete edit recipe so a raw vertical clip becomes a real Short.
    static func creativeBrief(
        for candidate: ShortCandidate,
        preset: BrandPreset
    ) -> ShortsCreativeBrief {
        let duration = max(candidate.duration, 1)
        let hookEnd = max(min(duration * 0.25, 5), 2)
        let buildEnd = max(duration - 4, hookEnd + 1)
        let hookCode = ShortCandidate.timecode(0) + "–" + ShortCandidate.timecode(hookEnd)
        let buildCode = ShortCandidate.timecode(hookEnd) + "–" + ShortCandidate.timecode(buildEnd)
        let endCode = ShortCandidate.timecode(buildEnd) + "–" + ShortCandidate.timecode(duration)

        let spoken = candidate.hookLine.trimmingCharacters(in: .whitespacesAndNewlines)
        let textIdea = spoken.isEmpty
            ? onScreenFallback(preset: preset)
            : spoken.uppercased()

        let music = musicIdeas(preset: preset)

        return ShortsCreativeBrief(
            storyShape: storyShape(preset: preset, duration: duration),
            beats: [
                "\(hookCode) HOOK — freeze or hard punch-in on the subject while the first line hits. Put big text on screen: “\(textIdea)”.",
                "\(buildCode) BUILD — stay on the find. Cut out footsteps, shelves, and dead air. Keep your reaction if it sells the moment.",
                "\(endCode) BUTTON — last 3–4 seconds: slight zoom, leave one question unanswered, say “full video on the channel.”"
            ],
            musicMood: music.mood,
            musicSearch: music.search,
            musicMixTip: music.mixTip,
            framingTips: framingTips(preset: preset, hasSpeech: !candidate.quote.isEmpty),
            onScreenText: textIdea,
            endingMove: endingMove(preset: preset)
        )
    }

    private static func storyShape(preset: BrandPreset, duration: TimeInterval) -> String {
        let lengthNote = duration <= 25
            ? "Keep it one idea only."
            : "One idea, but you have room for a tiny setup before the payoff."

        switch preset {
        case .halloweenHunt:
            return "Curiosity → creepy reveal → open loop. \(lengthNote)"
        case .storeWalk:
            return "Walk-up → spot the item → react / price / why it matters. \(lengthNote)"
        case .productReview:
            return "Claim → proof in-hand → honest verdict tease. \(lengthNote)"
        case .behindTheScenes:
            return "Setup → the interesting beat → invite to the full video. \(lengthNote)"
        case .custom:
            return "Hook → payoff → invite. \(lengthNote)"
        }
    }

    private static func musicIdeas(preset: BrandPreset) -> (mood: String, search: [String], mixTip: String) {
        switch preset {
        case .halloweenHunt:
            return (
                "Yes — put tense / eerie music under it. Sparse, not a full song with vocals.",
                ["dark ambient", "horror tension", "eerie piano", "halloween suspense"],
                "Duck music under your voice (−12 to −18 dB). Let a riser hit on the reveal, then cut music for the last spoken CTA."
            )
        case .storeWalk:
            return (
                "Yes — light upbeat or quirky shop beat behind the walk. Keep it playful.",
                ["lofi shop", "quirky ukulele", "upbeat casual", "retail vlog"],
                "Music stays low under talking. Bump it 2–3 dB in silent walking gaps, then drop again when you speak."
            )
        case .productReview:
            return (
                "Yes — clean modern bed, no big drops that fight your verdict.",
                ["modern corporate light", "tech review ambient", "soft electronic"],
                "Hold music flat under speech. A short hit on the product close-up is enough."
            )
        case .behindTheScenes:
            return (
                "Optional — soft ambient if the room tone is thin; skip music if tools/noise already fill it.",
                ["soft ambient", "workshop chill", "documentary bed"],
                "If you use music, keep it quieter than usual so real sound sells the BTS feel."
            )
        case .custom:
            return (
                "Yes — match the mood of the moment (tense, funny, or chill).",
                ["vlog beat", "cinematic tension", "funny comedy sting"],
                "Voice first. Music supports; it should never bury what you said."
            )
        }
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

        switch preset {
        case .halloweenHunt:
            tips.append("Hold an extra half-second on the spooky item after you name it — that silence sells the scare.")
        case .storeWalk:
            tips.append("Show the shelf tag / price if it’s readable; viewers love that detail.")
        case .productReview:
            tips.append("Insert one tight product insert (label, texture, button) mid-clip.")
        case .behindTheScenes:
            tips.append("If you’re talking to camera, keep eyes near the top third.")
        case .custom:
            break
        }

        return tips
    }

    private static func onScreenFallback(preset: BrandPreset) -> String {
        switch preset {
        case .halloweenHunt:
            return "WAIT FOR IT"
        case .storeWalk:
            return "FOUND THIS"
        case .productReview:
            return "HONEST TAKE"
        case .behindTheScenes:
            return "BEHIND THE SCENES"
        case .custom:
            return "WATCH THIS"
        }
    }

    private static func endingMove(preset: BrandPreset) -> String {
        switch preset {
        case .halloweenHunt:
            return "Freeze on the item, text “Full hunt on the channel,” soft whoosh out."
        case .storeWalk:
            return "Quick zoom on the find + “More aisle finds in the full video.”"
        case .productReview:
            return "Hold the product, text “Full review on the channel,” don’t give the final score here."
        case .behindTheScenes:
            return "Cut to a smile / wave and “Full video linked.”"
        case .custom:
            return "End on a question or unfinished beat so they tap the related long-form video."
        }
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
