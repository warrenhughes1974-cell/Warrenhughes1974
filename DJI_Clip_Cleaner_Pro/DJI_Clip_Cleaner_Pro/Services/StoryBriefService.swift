import Foundation

/// High-level story family for one finished video. Branding, copy, and
/// thumbnail targets follow this — not a fixed channel “look.”
enum StoryDomain: String, CaseIterable, Identifiable, Sendable {
    case travelDelay
    case retailHunt
    case cooking
    case motorsport
    case adventure
    case themePark
    case cruise
    case family
    case general

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .travelDelay: return "Travel / Delay"
        case .retailHunt: return "Retail / Shopping"
        case .cooking: return "Cooking / Food"
        case .motorsport: return "Motorsport / F1"
        case .adventure: return "Adventure"
        case .themePark: return "Theme Park"
        case .cruise: return "Cruise"
        case .family: return "Family / Lifestyle"
        case .general: return "General Story"
        }
    }
}

struct StoryBrief: Sendable {
    let domain: StoryDomain
    /// One-line search/snippet headline.
    let headline: String
    /// Short body that states what happened.
    let summary: String
    let places: [String]
    /// Story beats for the description list — never random snack nouns.
    let beats: [String]
    /// Words/phrases a good thumbnail should show or imply.
    let visualTargets: [String]
    /// Short burned-in thumbnail text (3–4 words).
    let thumbnailText: String
    let tags: [String]
    let hashtags: [String]
    let chapters: [TranscriptChapter]
    /// Only set when a Settings series actually fits this story.
    let seriesFits: Bool
}

/// Turns a transcript into a story brief that drives YouTube Prep.
///
/// This is deliberately not a retail “noun counter.” It looks for conflict,
/// place, and payoff language so delay vlogs, cooking days, F1, etc. each get
/// packaging that matches *that* story.
enum StoryBriefService {
    static func build(
        from transcript: Transcript?,
        hook: String,
        brand: BrandSettingsValues,
        extraPlaces: [String] = []
    ) -> StoryBrief {
        let text = (transcript?.fullText ?? "").lowercased()
        let hookClean = hook.trimmingCharacters(in: .whitespacesAndNewlines)
        let places = mergedPlaces(
            detected: TranscriptKeywordService.places(from: transcript),
            manual: extraPlaces
        )
        let domain = detectDomain(text: text, hook: hookClean, places: places)
        let beats = storyBeats(domain: domain, text: text, places: places, transcript: transcript)
        let headline = makeHeadline(
            domain: domain,
            hook: hookClean,
            places: places,
            text: text
        )
        let summary = makeSummary(
            domain: domain,
            places: places,
            beats: beats,
            text: text
        )
        let visuals = visualTargets(domain: domain, places: places, text: text)
        let thumb = thumbnailText(domain: domain, hook: hookClean, places: places, text: text)
        let tagList = makeTags(domain: domain, hook: hookClean, places: places, beats: beats)
        let hashes = makeHashtags(domain: domain, places: places)
        let seriesFits = seriesMatchesStory(
            series: brand.seriesName,
            domain: domain,
            text: text
        )

        return StoryBrief(
            domain: domain,
            headline: headline,
            summary: summary,
            places: places,
            beats: beats,
            visualTargets: visuals,
            thumbnailText: thumb,
            tags: tagList,
            hashtags: hashes,
            chapters: transcript.map {
                TranscriptionService.chapters(from: $0, storyDomain: domain)
            } ?? [],
            seriesFits: seriesFits
        )
    }

    // MARK: - Domain

    private static func detectDomain(
        text: String,
        hook: String,
        places: [String]
    ) -> StoryDomain {
        let haystack = (text + " " + hook.lowercased() + " " + places.joined(separator: " ")).lowercased()

        let travelHits = countHits(haystack, [
            "delay", "delayed", "delays", "flight", "airport", "airline", "airlines",
            "gate", "boarding", "ground stop", "ground delay", "missed", "canceled",
            "cancelled", "terminal", "dfw", "baggage", "layover", "tarmac"
        ])
        let retailHits = countHits(haystack, [
            "aisle", "shelf", "halloween", "homegoods", "marshalls", "ross",
            "walmart", "target", "clearance", "decorations", "animatronic"
        ])
        let cookingHits = countHits(haystack, [
            "recipe", "cook", "cooking", "bake", "baking", "kitchen", "oven",
            "grill", "ingredient", "dinner", "nachos", "taco", "pasta"
        ])
        let motorHits = countHits(haystack, [
            "formula", "f1", "grand prix", "racetrack", "pit lane", "qualifying",
            "nascar", "lap time", "motorsport", "paddock"
        ])
        let adventureHits = countHits(haystack, [
            "parachute", "skydiving", "skydive", "bungee", "zipline", "scuba",
            "hiking", "climb", "rafting"
        ])
        let parkHits = countHits(haystack, [
            "disney", "disneyland", "disney world", "universal", "theme park",
            "roller coaster", "magic kingdom"
        ])
        let cruiseHits = countHits(haystack, [
            "cruise", "embarkation", "cabin", "port day", "shore excursion",
            "royal caribbean", "carnival", "norwegian"
        ])

        let scored: [(StoryDomain, Int)] = [
            (.travelDelay, travelHits),
            (.retailHunt, retailHits),
            (.cooking, cookingHits),
            (.motorsport, motorHits),
            (.adventure, adventureHits),
            (.themePark, parkHits),
            (.cruise, cruiseHits)
        ]

        if let best = scored.max(by: { $0.1 < $1.1 }), best.1 >= 2 {
            return best.0
        }

        if !text.isEmpty {
            return .family
        }
        return .general
    }

    private static func countHits(_ text: String, _ needles: [String]) -> Int {
        needles.reduce(0) { partial, needle in
            partial + (text.contains(needle) ? 1 : 0)
        }
    }

    // MARK: - Beats / copy

    private static func storyBeats(
        domain: StoryDomain,
        text: String,
        places: [String],
        transcript: Transcript?
    ) -> [String] {
        var beats: [String] = []

        switch domain {
        case .travelDelay:
            let missedTrip = indicatesMissedTrip(text)
            if text.contains("ground") && (text.contains("delay") || text.contains("stop")) {
                beats.append("Nationwide ground delays")
            } else if text.contains("delay") {
                beats.append("Flight delays")
            }
            if missedTrip {
                beats.append("Missed business trip")
            } else if text.contains("business") && text.contains("trip") {
                beats.append("Business trip derailed")
            }
            if places.contains(where: { $0.uppercased() == "DFW" }) || text.contains("dfw") {
                beats.append("Stuck at DFW")
            }
            if text.contains("american") {
                beats.append("American Airlines chaos")
            }

        case .retailHunt:
            let topics = TranscriptKeywordService.topics(from: transcript, limit: 5)
            beats.append(contentsOf: topics)

        case .cooking:
            let topics = TranscriptKeywordService.topics(from: transcript, limit: 5)
            // Food nouns are the story here.
            beats.append(contentsOf: topics.prefix(4))
            if beats.isEmpty { beats.append("Home cooking") }

        case .motorsport:
            beats.append("Track day")
            if text.contains("f1") || text.contains("formula") {
                beats.append("Formula 1")
            }
            beats.append(contentsOf: places.prefix(2))

        case .adventure:
            if text.contains("skydive") || text.contains("parachute") {
                beats.append("Skydiving")
            }
            beats.append(contentsOf: places.prefix(2))

        case .themePark:
            if text.contains("disney") { beats.append("Disney day") }
            beats.append(contentsOf: places.prefix(3))

        case .cruise:
            beats.append("Cruise day")
            beats.append(contentsOf: places.prefix(3))

        case .family, .general:
            // Prefer places + strong story topics; skip snack noise unless cooking.
            let topics = TranscriptKeywordService.topics(from: transcript, limit: 6)
                .filter { !isNoiseBeat($0) }
            beats.append(contentsOf: places.prefix(2))
            beats.append(contentsOf: topics.prefix(3))
        }

        return uniqued(beats).prefix(5).map { $0 }
    }

    private static func isNoiseBeat(_ phrase: String) -> Bool {
        let lower = phrase.lowercased()
        let noise: Set<String> = [
            "nachos", "soda", "water", "coffee", "snack", "snacks",
            "internet speed", "brand ups", "downstairs area"
        ]
        if noise.contains(lower) { return true }
        return noise.contains { lower == $0 || lower.contains($0) }
    }

    private static func makeHeadline(
        domain: StoryDomain,
        hook: String,
        places: [String],
        text: String
    ) -> String {
        let placeBit = places.isEmpty
            ? ""
            : " at \(sentenceList(Array(places.prefix(2))))"

        switch domain {
        case .travelDelay:
            let airline = text.contains("american") ? "American Airlines " : ""
            if indicatesMissedTrip(text) {
                return "\(airline)ground delays made us miss our business trip."
            }
            if text.contains("business") && text.contains("trip") {
                return "\(airline)ground delays derailed our business trip."
            }
            if !hook.isEmpty, hook.split(separator: " ").count <= 6 {
                return "\(titleCase(hook)) — ground delays\(placeBit) turned this trip upside down."
            }
            return "\(airline)ground delays\(placeBit) turned this trip upside down."

        case .retailHunt:
            return hook.isEmpty
                ? "Store finds\(placeBit) worth the trip."
                : "\(titleCase(hook)) — the finds\(placeBit) worth seeing."

        case .cooking:
            return hook.isEmpty
                ? "Cooking day in the kitchen."
                : "\(titleCase(hook)) — from the kitchen."

        case .motorsport:
            return hook.isEmpty
                ? "Race day energy\(placeBit)."
                : "\(titleCase(hook)) — race day\(placeBit)."

        case .adventure:
            return hook.isEmpty
                ? "An adventure day worth watching."
                : "\(titleCase(hook)) — the full adventure."

        case .themePark:
            return hook.isEmpty
                ? "Theme park day\(placeBit)."
                : "\(titleCase(hook)) — park day\(placeBit)."

        case .cruise:
            return hook.isEmpty
                ? "Cruise day stories."
                : "\(titleCase(hook)) — cruise day."

        case .family, .general:
            if !hook.isEmpty {
                return "\(titleCase(hook)) — here’s what actually happened."
            }
            return "Here’s what actually happened in this video."
        }
    }

    private static func makeSummary(
        domain: StoryDomain,
        places: [String],
        beats: [String],
        text: String
    ) -> String {
        var sentences: [String] = []

        switch domain {
        case .travelDelay:
            let hasDFW = places.contains { $0.uppercased() == "DFW" }
            let destinations = places.filter { $0.uppercased() != "DFW" }
            if indicatesMissedTrip(text) {
                if hasDFW, let destination = destinations.first {
                    sentences.append(
                        "Massive ground delays at DFW kept us from making our business trip to \(destination)."
                    )
                } else {
                    sentences.append(
                        "Massive ground delays kept us from making our business trip."
                    )
                }
            } else if text.contains("business") && text.contains("trip") {
                sentences.append(
                    "What should have been a business trip became hours of delays and waiting."
                )
            } else {
                sentences.append(
                    "This travel day went sideways — delays, waiting, and a plan that fell apart."
                )
            }
            if hasDFW {
                sentences.append("The problem started at DFW as delays spread across the system.")
            }

        case .retailHunt:
            sentences.append("A store walk for the finds that actually stood out.")
            if !places.isEmpty {
                sentences.append("We stopped at \(sentenceList(places)).")
            }

        case .cooking:
            sentences.append("A cooking video from start to finish — what we made and how it went.")

        case .motorsport:
            sentences.append("Race-day footage and the moments around the track.")

        case .adventure:
            sentences.append("An adventure day captured as it happened.")

        case .themePark:
            sentences.append("A theme-park day with the rides, waits, and family chaos.")

        case .cruise:
            sentences.append("Cruise-day stories from onboard and ashore.")

        case .family, .general:
            sentences.append("A real day-in-the-life video — what happened, in order.")
        }

        if domain == .retailHunt, !beats.isEmpty {
            sentences.append("Along the way we found \(sentenceList(beats.map { $0.lowercased() })).")
        }

        sentences.append("Watch through for how the day actually unfolded.")
        return sentences.joined(separator: " ")
    }

    private static func visualTargets(
        domain: StoryDomain,
        places: [String],
        text: String
    ) -> [String] {
        var targets: [String] = []

        switch domain {
        case .travelDelay:
            targets += [
                "airplane", "aircraft", "airport", "jet", "terminal",
                "gate", "delay", "flight", "baggage", "tarmac"
            ]
            if text.contains("american") {
                targets += ["american", "airlines"]
            }
            targets += places.map { $0.lowercased() }

        case .retailHunt:
            targets += ["store", "shelf", "aisle", "shopping"]
            targets += places.map { $0.lowercased() }

        case .cooking:
            targets += ["food", "kitchen", "cooking", "meal", "plate", "recipe"]

        case .motorsport:
            targets += ["car", "race", "track", "formula", "motorsport", "pit"]

        case .adventure:
            targets += ["sky", "parachute", "mountain", "adventure", "jump"]

        case .themePark:
            targets += ["castle", "ride", "park", "disney", "roller"]

        case .cruise:
            targets += ["ship", "cruise", "ocean", "deck", "port"]

        case .family, .general:
            targets += places.map { $0.lowercased() }
        }

        return uniqued(targets)
    }

    private static func thumbnailText(
        domain: StoryDomain,
        hook: String,
        places: [String],
        text: String
    ) -> String {
        // Strip cheesy punctuation/emoji the user (or old presets) may have typed.
        let cleanedHook = hook
            .replacingOccurrences(of: "🎃", with: " ")
            .replacingOccurrences(of: "!!", with: " ")
            .replacingOccurrences(of: "!", with: " ")
            .replacingOccurrences(
                of: "[^A-Za-z0-9 \\-]",
                with: " ",
                options: .regularExpression
            )

        switch domain {
        case .travelDelay:
            if indicatesMissedTrip(text) {
                return "MISSED OUR FLIGHT"
            }
            if places.contains(where: { $0.uppercased() == "DFW" }) || text.contains("dfw") {
                return "DFW GROUND DELAYS"
            }
            if text.contains("american") {
                return "AIRLINE DELAY CHAOS"
            }
            return "FLIGHT DELAY CHAOS"

        case .cooking:
            return shortThumb(from: cleanedHook, fallback: "COOKING DAY")

        case .motorsport:
            return shortThumb(from: cleanedHook, fallback: "RACE DAY")

        case .adventure:
            return shortThumb(from: cleanedHook, fallback: "ADVENTURE DAY")

        case .themePark:
            return shortThumb(from: cleanedHook, fallback: "PARK DAY")

        case .cruise:
            return shortThumb(from: cleanedHook, fallback: "CRUISE DAY")

        case .retailHunt:
            return shortThumb(from: cleanedHook, fallback: "STORE FINDS")

        case .family, .general:
            return shortThumb(from: cleanedHook, fallback: "REAL DAY")
        }
    }

    private static func shortThumb(from hook: String, fallback: String) -> String {
        let filler: Set<String> = [
            "a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for", "with"
        ]
        let words = hook
            .split(separator: " ")
            .map(String.init)
            .filter { !$0.isEmpty && !filler.contains($0.lowercased()) }

        if words.isEmpty { return fallback }
        return words.prefix(4).map { $0.uppercased() }.joined(separator: " ")
    }

    private static func makeTags(
        domain: StoryDomain,
        hook: String,
        places: [String],
        beats: [String]
    ) -> [String] {
        var tags: [String] = []
        func add(_ value: String) {
            let t = value.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            guard t.split(separator: " ").count >= 2 || t.count >= 5 else { return }
            guard !tags.contains(t) else { return }
            tags.append(t)
        }

        let cleanHook = hook.lowercased()
        if !cleanHook.isEmpty { add(cleanHook) }

        switch domain {
        case .travelDelay:
            add("flight delay")
            add("airport delay")
            add("ground delay")
            add("travel vlog")
            add("missed flight")
            add("american airlines delay")
        case .retailHunt:
            add("store walk")
            add("shop with me")
        case .cooking:
            add("cooking vlog")
            add("home cooking")
        case .motorsport:
            add("race day vlog")
            add("motorsport vlog")
        case .adventure:
            add("adventure vlog")
        case .themePark:
            add("theme park vlog")
            add("disney family")
        case .cruise:
            add("cruise vlog")
        case .family, .general:
            add("family vlog")
            add("day in the life")
        }

        for place in places.prefix(3) {
            add("\(place.lowercased()) vlog")
            if domain == .travelDelay {
                add("\(place.lowercased()) delay")
            }
        }

        for beat in beats.prefix(3) {
            add(beat)
        }

        return Array(tags.prefix(15))
    }

    private static func indicatesMissedTrip(_ text: String) -> Bool {
        let phrases = [
            "missed",
            "miss my",
            "miss our",
            "didn't make",
            "didnt make",
            "never made",
            "not going to make",
            "couldn't get",
            "couldnt get",
            "had to cancel",
            "trip was canceled",
            "trip was cancelled"
        ]
        return phrases.contains { text.contains($0) }
    }

    private static func makeHashtags(domain: StoryDomain, places: [String]) -> [String] {
        var tags: [String] = []
        func add(_ raw: String) {
            let compact = raw
                .components(separatedBy: CharacterSet.alphanumerics.inverted)
                .joined()
            guard compact.count >= 3 else { return }
            let tag = "#\(compact.lowercased())"
            guard !tags.contains(tag) else { return }
            tags.append(tag)
        }

        switch domain {
        case .travelDelay:
            add("flightdelay"); add("travelvlog")
        case .retailHunt:
            add("storewalk"); add("shopwithme")
        case .cooking:
            add("cooking"); add("foodvlog")
        case .motorsport:
            add("f1"); add("raceday")
        case .adventure:
            add("adventure"); add("adrenaline")
        case .themePark:
            add("disney"); add("themepark")
        case .cruise:
            add("cruise"); add("cruiselife")
        case .family, .general:
            add("familyvlog"); add("travel")
        }

        for place in places.prefix(1) {
            add(place)
        }

        return Array(tags.prefix(3))
    }

    /// Halloween Hunt (etc.) must not leak onto unrelated stories.
    private static func seriesMatchesStory(
        series: String,
        domain: StoryDomain,
        text: String
    ) -> Bool {
        let seriesLower = series.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !seriesLower.isEmpty else { return false }

        if seriesLower.contains("halloween") || seriesLower.contains("spooky") {
            return domain == .retailHunt && (
                text.contains("halloween") || text.contains("spooky") || text.contains("pumpkin")
            )
        }
        if seriesLower.contains("store") {
            return domain == .retailHunt
        }
        if seriesLower.contains("cruise") {
            return domain == .cruise || text.contains("cruise")
        }
        if seriesLower.contains("disney") {
            return domain == .themePark || text.contains("disney")
        }
        // Custom named series: only keep if the words appear in the story.
        let tokens = seriesLower.split(separator: " ").map(String.init).filter { $0.count > 2 }
        guard !tokens.isEmpty else { return false }
        return tokens.contains { text.contains($0) }
    }

    // MARK: - Helpers

    private static func mergedPlaces(detected: [String], manual: [String]) -> [String] {
        var result: [String] = []
        for value in manual + detected {
            let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !trimmed.isEmpty else { continue }
            guard !result.contains(where: { $0.caseInsensitiveCompare(trimmed) == .orderedSame }) else {
                continue
            }
            result.append(trimmed)
        }
        return Array(result.prefix(6))
    }

    private static func sentenceList(_ items: [String]) -> String {
        switch items.count {
        case 0: return ""
        case 1: return items[0]
        case 2: return "\(items[0]) and \(items[1])"
        default:
            return items.dropLast().joined(separator: ", ") + ", and \(items[items.count - 1])"
        }
    }

    private static func uniqued(_ items: [String]) -> [String] {
        var seen = Set<String>()
        var out: [String] = []
        for item in items {
            let key = item.lowercased()
            guard !key.isEmpty, !seen.contains(key) else { continue }
            seen.insert(key)
            out.append(item)
        }
        return out
    }

    private static func titleCase(_ value: String) -> String {
        let lowercaseWords: Set<String> = [
            "a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for", "with"
        ]
        let words = value
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .split(separator: " ")
        return words.enumerated().map { index, word in
            let lower = word.lowercased()
            if index > 0, lowercaseWords.contains(lower) { return lower }
            return lower.prefix(1).uppercased() + lower.dropFirst()
        }
        .joined(separator: " ")
    }
}
