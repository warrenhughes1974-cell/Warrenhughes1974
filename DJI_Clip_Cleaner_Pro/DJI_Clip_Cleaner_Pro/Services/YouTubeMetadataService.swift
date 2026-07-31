import Foundation

enum MetadataQualityLevel: Sendable {
    case good
    case warning
    case problem
}

struct MetadataQuality: Sendable {
    let level: MetadataQualityLevel
    let message: String
}

struct YouTubeMetadata: Sendable {
    let title: String
    let thumbnailText: String
    let description: String
    let tags: [String]

    var tagsLine: String {
        tags.joined(separator: ", ")
    }
}

enum YouTubeMetadataService {
    static let uploadFolderName = "YouTube_Prep"

    /// YouTube truncates around here on desktop search and mobile browse.
    static let recommendedTitleLimit = 60
    static let hardTitleLimit = 100

    /// Only this much of a description shows in search snippets and above "Show more".
    static let descriptionSnippetLimit = 150

    /// YouTube counts commas and spaces against this budget.
    static let tagCharacterLimit = 500
    static let maxThumbnailWords = 4

    // MARK: - Title

    /// Builds a search-friendly title. The channel name is deliberately not
    /// front-loaded because YouTube already shows it under every video, and the
    /// first ~40 characters carry the most ranking and click-through weight.
    static func buildTitle(
        hook: String,
        brand: BrandSettingsValues,
        includeChannel: Bool = false
    ) -> String {
        let cleanHook = titleCase(hook)
        let series = brand.seriesName.trimmingCharacters(in: .whitespacesAndNewlines)
        let channel = brand.channelPrefix.trimmingCharacters(in: .whitespacesAndNewlines)

        guard !cleanHook.isEmpty else {
            return series.isEmpty ? "" : series
        }

        var title = cleanHook

        if !series.isEmpty, !cleanHook.localizedCaseInsensitiveContains(series) {
            let withSeries = "\(cleanHook) | \(series)"
            if withSeries.count <= recommendedTitleLimit {
                title = withSeries
            }
        }

        if includeChannel, !channel.isEmpty {
            let withChannel = "\(title) | \(channel)"
            if withChannel.count <= hardTitleLimit {
                title = withChannel
            }
        }

        return title
    }

    static func titleQuality(_ title: String) -> MetadataQuality {
        let count = title.count

        if count == 0 {
            return MetadataQuality(level: .problem, message: "Type a hook to build your title.")
        }

        if count > hardTitleLimit {
            return MetadataQuality(
                level: .problem,
                message: "\(count) characters — YouTube cuts off at \(hardTitleLimit)."
            )
        }

        if count > recommendedTitleLimit {
            return MetadataQuality(
                level: .warning,
                message: "\(count) characters — mobile may truncate. Aim for \(recommendedTitleLimit) or fewer."
            )
        }

        if count < 30 {
            return MetadataQuality(
                level: .warning,
                message: "\(count) characters — short titles waste search space. Aim for 40–60."
            )
        }

        return MetadataQuality(level: .good, message: "\(count) characters — good length for search and mobile.")
    }

    // MARK: - Thumbnail text

    /// Thumbnail text should complement the title, not repeat it. Three or four
    /// large words read on a phone; a full sentence does not.
    /// Prefer story/payoff words (delay, missed, stuck) over leading brand names.
    static func thumbnailText(from hook: String) -> String {
        let filler: Set<String> = [
            "a", "an", "the", "and", "or", "of", "in", "on", "at",
            "to", "for", "with", "my", "our", "this", "that", "is", "was"
        ]
        let brandLeaders: Set<String> = [
            "american", "airlines", "airline", "southwest", "delta", "united",
            "spirit", "frontier", "jetblue"
        ]
        let payoff: Set<String> = [
            "delay", "delays", "delayed", "missed", "stuck", "cancelled",
            "canceled", "hours", "late", "dfw", "ground", "trip", "business",
            "chaos", "ruined", "nightmare"
        ]

        let words = hook
            .split(whereSeparator: { $0 == " " || $0 == "·" || $0 == "|" || $0 == "—" || $0 == "-" })
            .map { String($0).trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }

        guard !words.isEmpty else { return "" }

        let meaningful = words.filter { !filler.contains($0.lowercased()) }
        let pool = meaningful.isEmpty ? words : meaningful

        let payoffWords = pool.filter { payoff.contains($0.lowercased()) }
        let nonBrand = pool.filter { !brandLeaders.contains($0.lowercased()) }

        let chosen: ArraySlice<String>
        if payoffWords.count >= 2 {
            chosen = payoffWords.prefix(maxThumbnailWords)
        } else if payoffWords.count == 1, nonBrand.count >= 2 {
            // e.g. "DFW" + "DELAYS" from a longer hook that starts with a brand.
            var mixed = payoffWords
            for word in nonBrand where !payoff.contains(word.lowercased()) {
                mixed.append(word)
                if mixed.count >= maxThumbnailWords { break }
            }
            chosen = mixed.prefix(maxThumbnailWords)
        } else if nonBrand.count >= 2 {
            chosen = nonBrand.prefix(maxThumbnailWords)
        } else {
            chosen = pool.prefix(maxThumbnailWords)
        }

        return chosen
            .map { $0.uppercased() }
            .joined(separator: " ")
    }

    static func thumbnailTextQuality(_ text: String) -> MetadataQuality {
        let words = text.split(separator: " ").count

        if words == 0 {
            return MetadataQuality(level: .problem, message: "Add short thumbnail text.")
        }

        if words > maxThumbnailWords {
            return MetadataQuality(
                level: .warning,
                message: "\(words) words — 3 to 4 words read best on a phone."
            )
        }

        return MetadataQuality(level: .good, message: "\(words) word(s) — reads clearly at small sizes.")
    }

    // MARK: - Description

    static func generateDescription(
        hook: String,
        brand: BrandSettingsValues,
        preset: BrandPreset,
        transcript: Transcript? = nil,
        extraPlaces: [String] = [],
        confirmedBrief: StoryBrief? = nil,
        confirmedAnalysis: StoryAnalysis? = nil
    ) -> String {
        let channel = brand.channelPrefix.trimmingCharacters(in: .whitespacesAndNewlines)
        let series = brand.seriesName.trimmingCharacters(in: .whitespacesAndNewlines)
        let cleanHook = titleCase(hook)

        let brief = confirmedBrief ?? StoryBriefService.build(
            from: transcript,
            hook: cleanHook,
            brand: brand,
            extraPlaces: extraPlaces
        )

        let narrative = confirmedAnalysis.map(narrativeBody(from:))
            ?? cleanedNarrative(brief.summary)
        let snippet = searchSnippet(
            from: confirmedAnalysis,
            fallbackHeadline: brief.headline,
            hook: cleanHook
        )

        var lines: [String] = []

        // Search snippet = first visible lines in YouTube search.
        lines.append(trimmedSnippet(snippet))
        lines.append("")
        lines.append(narrative)

        let places = descriptionPlaces(brief.places)
        if !places.isEmpty {
            lines.append("")
            lines.append(brief.domain == .retailHunt ? "STORES IN THIS VIDEO" : "PLACES IN THIS VIDEO")
            for place in places {
                lines.append("· \(place)")
            }
        }

        // Product/store videos benefit from an item list. Story videos do not:
        // the natural summary already explains the plot without repeating bullets.
        if brief.domain == .retailHunt, !brief.beats.isEmpty {
            lines.append("")
            lines.append("WHAT WE FOUND")
            for beat in brief.beats {
                lines.append("· \(beat)")
            }
        }

        let chapters = !brief.chapters.isEmpty
            ? brief.chapters
            : transcript.map {
                TranscriptionService.chapters(from: $0, storyDomain: brief.domain)
            } ?? []
        if chapters.count > 1 {
            lines.append("")
            lines.append("CHAPTERS")
            for chapter in chapters {
                lines.append(chapter.formattedLine)
            }
        }

        lines.append("")
        lines.append(callToAction(channel: channel, domain: brief.domain))
        lines.append("")

        // Only advertise a playlist when the series fits *this* story.
        if brief.seriesFits, !series.isEmpty {
            lines.append("MORE FROM THIS SERIES")
            lines.append("Watch the full \(series) playlist on the channel.")
            lines.append("")
        }

        lines.append("GEAR & WORKFLOW")
        lines.append("Filmed on DJI · Edited in Filmora")

        let hashtags = brief.hashtags.isEmpty
            ? []
            : brief.hashtags
        if !hashtags.isEmpty {
            lines.append("")
            lines.append(hashtags.joined(separator: " "))
        }

        return lines.joined(separator: "\n")
    }

    /// Paste-ready brief for ChatGPT/Grok so cloud models polish copy without
    /// inventing cast, places, or outcomes beyond the confirmed story.
    static func chatGPTPack(
        analysis: StoryAnalysis,
        title: String,
        brand: BrandSettingsValues,
        transcript: Transcript?,
        extraPlaces: [String] = []
    ) -> String {
        let places = descriptionPlaces(uniquePlaces(
            origin: analysis.origin,
            problemLocation: analysis.problemLocation,
            destination: analysis.destination,
            extra: extraPlaces
        ))
        let chapters = analysis.chapters
            .sorted { $0.startTime < $1.startTime }
            .map { chapter in
                let stamp = TranscriptChapter.timecode(chapter.startTime)
                return "\(stamp) \(chapter.title)"
            }

        var lines: [String] = [
            "You are helping write YouTube metadata for a real video.",
            "Use ONLY the confirmed facts below. Do not invent travelers, pets on the trip, places, or outcomes.",
            "If a fact is missing, leave it out or keep it vague — never guess.",
            "",
            "CHANNEL: \(brand.channelPrefix.isEmpty ? "Fun Now Run Later" : brand.channelPrefix)",
            "STORY TYPE: \(analysis.domain.displayName)",
            "",
            "PREFERRED TITLE:",
            title.isEmpty ? analysis.titleIdeas.first ?? analysis.subject : title,
            "",
            "TITLE IDEAS:",
        ]

        let titles = analysis.titleIdeas.isEmpty ? [analysis.subject] : analysis.titleIdeas
        for idea in titles.prefix(6) {
            lines.append("- \(idea)")
        }

        lines.append("")
        lines.append("CONFIRMED STORY FACTS:")
        lines.append("- Subject: \(blankToUnknown(analysis.subject))")
        lines.append("- Goal: \(blankToUnknown(analysis.goal))")
        lines.append("- Obstacle: \(blankToUnknown(analysis.obstacle))")
        lines.append("- Origin: \(blankToUnknown(analysis.origin))")
        lines.append("- Problem happened at: \(blankToUnknown(analysis.problemLocation))")
        lines.append("- Destination: \(blankToUnknown(analysis.destination))")
        lines.append("- Outcome: \(blankToUnknown(analysis.outcome))")
        lines.append("- Summary: \(blankToUnknown(analysis.summary))")

        if !places.isEmpty {
            lines.append("")
            lines.append("PLACES:")
            for place in places {
                lines.append("- \(place)")
            }
        }

        if !analysis.tags.isEmpty {
            lines.append("")
            lines.append("TAG IDEAS:")
            for tag in analysis.tags.prefix(12) {
                lines.append("- \(tag)")
            }
        }

        if !analysis.hashtags.isEmpty {
            lines.append("")
            lines.append("HASHTAGS: \(analysis.hashtags.joined(separator: " "))")
        }

        if !chapters.isEmpty {
            lines.append("")
            lines.append("CHAPTERS:")
            for chapter in chapters.prefix(12) {
                lines.append("- \(chapter)")
            }
        }

        lines.append("")
        lines.append("WRITE:")
        lines.append("1) One strong YouTube title (under 70 characters)")
        lines.append("2) A natural description: 2–4 sentence story hook, then optional Places / Chapters / CTA / hashtags")
        lines.append("3) Keep American conversational voice — not corporate, not clickbait spam")
        lines.append("4) Do not mention anyone who is not supported as being on this trip/event")

        if let transcript, !transcript.isEmpty {
            let text = transcript.fullText.trimmingCharacters(in: .whitespacesAndNewlines)
            let clipped = text.count > 6_000
                ? String(text.prefix(6_000)) + "\n…[transcript truncated]…"
                : text
            lines.append("")
            lines.append("TRANSCRIPT (for wording/tone only; facts above still win on conflicts):")
            lines.append(clipped)
        }

        return lines.joined(separator: "\n")
    }

    /// Builds a complete description paragraph from confirmed Story Review fields.
    /// Prefers a usable edited summary; otherwise synthesizes plain English from slots.
    static func narrativeBody(from analysis: StoryAnalysis) -> String {
        let summary = cleanedNarrative(analysis.summary)
        if isUsableNarrative(summary) {
            return ensureSentenceEnding(summary)
        }

        var sentences: [String] = []
        let subject = cleanPhrase(analysis.subject)
        let goal = cleanPhrase(analysis.goal)
        let obstacle = cleanPhrase(analysis.obstacle)
        let origin = cleanPhrase(analysis.origin)
        let problem = cleanPhrase(analysis.problemLocation)
        let destination = cleanPhrase(analysis.destination)
        let outcome = cleanPhrase(analysis.outcome)

        switch analysis.domain {
        case .travelDelay:
            if !origin.isEmpty && !destination.isEmpty {
                sentences.append("I was headed from \(origin) to \(destination).")
            } else if !destination.isEmpty {
                sentences.append("I was headed to \(destination).")
            } else if !subject.isEmpty {
                sentences.append(ensureSentenceEnding(subject))
            }

            if !obstacle.isEmpty && !problem.isEmpty {
                sentences.append("\(capitalizeFirst(obstacle)) hit at \(problem).")
            } else if !obstacle.isEmpty {
                sentences.append(ensureSentenceEnding(capitalizeFirst(obstacle)))
            } else if !problem.isEmpty {
                sentences.append("Things went sideways at \(problem).")
            }

            if !outcome.isEmpty {
                sentences.append(ensureSentenceEnding(capitalizeFirst(outcome)))
            } else if !goal.isEmpty {
                sentences.append(ensureSentenceEnding(capitalizeFirst(goal)))
            }

        default:
            if !subject.isEmpty {
                sentences.append(ensureSentenceEnding(capitalizeFirst(subject)))
            }
            if !goal.isEmpty {
                sentences.append(ensureSentenceEnding(capitalizeFirst(goal)))
            }
            if !obstacle.isEmpty {
                sentences.append(ensureSentenceEnding(capitalizeFirst(obstacle)))
            }
            if !origin.isEmpty || !problem.isEmpty || !destination.isEmpty {
                var placeBits: [String] = []
                if !origin.isEmpty { placeBits.append("started in \(origin)") }
                if !problem.isEmpty { placeBits.append("key moment at \(problem)") }
                if !destination.isEmpty { placeBits.append("headed for \(destination)") }
                if !placeBits.isEmpty {
                    sentences.append(ensureSentenceEnding(capitalizeFirst(placeBits.joined(separator: ", "))))
                }
            }
            if !outcome.isEmpty {
                sentences.append(ensureSentenceEnding(capitalizeFirst(outcome)))
            }
        }

        let joined = sentences.joined(separator: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        if joined.isEmpty {
            return "Confirm the story details above, then generate the description again."
        }
        return joined
    }

    private static func trimmedSnippet(_ snippet: String) -> String {
        guard snippet.count > descriptionSnippetLimit else {
            return snippet
        }
        return String(snippet.prefix(descriptionSnippetLimit - 1))
            .trimmingCharacters(in: .whitespaces) + "…"
    }

    private static func searchSnippet(
        from analysis: StoryAnalysis?,
        fallbackHeadline: String,
        hook: String
    ) -> String {
        if let analysis {
            let obstacle = cleanPhrase(analysis.obstacle)
            let problem = cleanPhrase(analysis.problemLocation)
            let destination = cleanPhrase(analysis.destination)
            let subject = cleanPhrase(analysis.subject)

            if !problem.isEmpty && !destination.isEmpty {
                let lead = obstacle.isEmpty ? (subject.isEmpty ? "Travel day" : subject) : obstacle
                return "\(capitalizeFirst(lead)) at \(problem) — headed to \(destination)"
            }
            if !obstacle.isEmpty && !problem.isEmpty {
                return "\(capitalizeFirst(obstacle)) at \(problem)"
            }
            if let title = analysis.titleIdeas.first, isUsableNarrative(title) || title.split(separator: " ").count >= 4 {
                return title
            }
            if !subject.isEmpty, subject.split(separator: " ").count >= 3 {
                return capitalizeFirst(subject)
            }
        }

        let headline = cleanPhrase(fallbackHeadline)
        if !headline.isEmpty, headline.split(separator: " ").count >= 3 {
            return headline
        }
        let hookClean = cleanPhrase(hook)
        if !hookClean.isEmpty {
            return titleCase(hookClean)
        }
        return headline.isEmpty ? "Video story" : headline
    }

    private static func cleanedNarrative(_ value: String) -> String {
        var text = value.trimmingCharacters(in: .whitespacesAndNewlines)
        // Scrub common broken openings left after cast removal.
        while let match = text.range(
            of: #"^(and|or|but|so)\s+"#,
            options: [.regularExpression, .caseInsensitive]
        ) {
            text = String(text[match.upperBound...])
                .trimmingCharacters(in: .whitespacesAndNewlines)
        }
        return text
    }

    private static func isUsableNarrative(_ value: String) -> Bool {
        let text = cleanedNarrative(value)
        guard text.count >= 40 else { return false }
        guard text.first?.isLetter == true else { return false }
        let lower = text.lowercased()
        let badStarts = ["goal:", "obstacle:", "outcome:", "subject:"]
        if badStarts.contains(where: { lower.hasPrefix($0) }) {
            return false
        }
        return text.split(separator: " ").count >= 8
    }

    private static func descriptionPlaces(_ places: [String]) -> [String] {
        let generic: Set<String> = [
            "airport", "hotel", "office", "terminal", "gate", "plane", "flight"
        ]
        let specific = places.filter { !generic.contains($0.lowercased()) }
        // Prefer specific places (DFW, Omaha). Fall back to generics only if that
        // is all the confirmed story has.
        return specific.isEmpty ? places : specific
    }

    private static func uniquePlaces(
        origin: String,
        problemLocation: String,
        destination: String,
        extra: [String]
    ) -> [String] {
        var output: [String] = []
        for value in [origin, problemLocation, destination] + extra {
            let clean = value.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !clean.isEmpty else { continue }
            guard !output.contains(where: { $0.caseInsensitiveCompare(clean) == .orderedSame }) else {
                continue
            }
            output.append(clean)
        }
        return output
    }

    private static func blankToUnknown(_ value: String) -> String {
        let clean = value.trimmingCharacters(in: .whitespacesAndNewlines)
        return clean.isEmpty ? "(unknown)" : clean
    }

    private static func cleanPhrase(_ value: String) -> String {
        value.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private static func ensureSentenceEnding(_ value: String) -> String {
        let clean = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !clean.isEmpty else { return "" }
        if let last = clean.last, ".!?".contains(last) {
            return clean
        }
        return clean + "."
    }

    private static func capitalizeFirst(_ value: String) -> String {
        let clean = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let first = clean.first else { return "" }
        return first.uppercased() + clean.dropFirst()
    }

    static func descriptionQuality(_ description: String) -> MetadataQuality {
        guard !description.isEmpty else {
            return MetadataQuality(level: .problem, message: "Generate a description.")
        }

        let firstLine = description
            .components(separatedBy: "\n")
            .first ?? ""

        if firstLine.count > descriptionSnippetLimit {
            return MetadataQuality(
                level: .warning,
                message: "Opening line is \(firstLine.count) characters — only the first \(descriptionSnippetLimit) show in search."
            )
        }

        return MetadataQuality(
            level: .good,
            message: "Opening line is \(firstLine.count)/\(descriptionSnippetLimit) characters — fits the search snippet."
        )
    }

    // MARK: - Tags

    /// Ordered most specific first. YouTube weights the first tags more heavily
    /// and treats single broad words as noise, so every tag here is a phrase.
    static func generateTags(
        hook: String,
        brand: BrandSettingsValues,
        preset: BrandPreset,
        transcript: Transcript? = nil,
        extraPlaces: [String] = [],
        confirmedBrief: StoryBrief? = nil
    ) -> [String] {
        let cleanHook = tagSafe(hook)
        let channel = brand.channelPrefix.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let brief = confirmedBrief ?? StoryBriefService.build(
            from: transcript,
            hook: hook,
            brand: brand,
            extraPlaces: extraPlaces
        )

        var tags: [String] = []

        func append(_ value: String, allowSingleWord: Bool = false) {
            let trimmed = value
                .trimmingCharacters(in: .whitespacesAndNewlines)
                .lowercased()

            guard !trimmed.isEmpty else { return }
            guard allowSingleWord || trimmed.split(separator: " ").count >= 2 else { return }
            guard !tags.contains(trimmed) else { return }

            let projected = (tags + [trimmed]).joined(separator: ", ")
            guard projected.count <= tagCharacterLimit else { return }

            tags.append(trimmed)
        }

        append(cleanHook, allowSingleWord: true)

        // Story tags first — never Halloween Hunt on a delay video.
        for tag in brief.tags {
            append(tag)
        }

        if brief.seriesFits {
            let series = brand.seriesName.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            if !series.isEmpty {
                append("\(cleanHook) \(series)")
                append(series)
            }
        }

        // Retail presets can still add store-hunt phrases when the *story* is retail.
        if brief.domain == .retailHunt {
            for tag in presetTags(preset) {
                append(tag)
            }
        }

        if !channel.isEmpty {
            append("\(channel) vlog")
        }

        return Array(tags.prefix(15))
    }

    static func tagsQuality(_ tags: [String]) -> MetadataQuality {
        let line = tags.joined(separator: ", ")

        if tags.isEmpty {
            return MetadataQuality(level: .problem, message: "Generate tags.")
        }

        if line.count > tagCharacterLimit {
            return MetadataQuality(
                level: .problem,
                message: "\(line.count)/\(tagCharacterLimit) characters — over YouTube's limit."
            )
        }

        if tags.count < 5 {
            return MetadataQuality(
                level: .warning,
                message: "\(tags.count) tags — aim for 8 to 15."
            )
        }

        return MetadataQuality(
            level: .good,
            message: "\(tags.count) tags · \(line.count)/\(tagCharacterLimit) characters."
        )
    }

    // MARK: - Hook suggestion

    /// Export filenames carry timestamps, "(copy)", and camera prefixes. None of
    /// that belongs in a title, so it is stripped before the name is offered as
    /// a starting hook.
    static func hookSuggestion(from videoURL: URL, fallbackSeries: String = "") -> String {
        let baseName = videoURL.deletingPathExtension().lastPathComponent
        var cleaned = baseName
            .replacingOccurrences(of: "_", with: " ")
            .replacingOccurrences(of: "-", with: " ")

        let noise = [
            "\\([^)]*copy[^)]*\\)",
            "\\bcopy\\s*\\d*\\b",
            "\\b\\d{4}[ ]\\d{2}[ ]\\d{2}\\b",
            "\\b\\d{2}[ ]\\d{2}[ ]\\d{2}\\b",
            "\\b\\d{8,}\\b",
            "\\b(?:dji|gopr|gx|img|mvi|mov|vid|clip|seq)\\s*\\d*\\b",
            "\\b(?:final|finished|export|render|edit|master|draft)\\b",
            "\\bv\\d+\\b"
        ]

        for pattern in noise {
            cleaned = cleaned.replacingOccurrences(
                of: pattern,
                with: " ",
                options: [.regularExpression, .caseInsensitive]
            )
        }

        // Anything left that is only digits was part of a stamp, not a topic.
        cleaned = cleaned
            .split(separator: " ")
            .filter { !$0.allSatisfy(\.isNumber) }
            .joined(separator: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)

        guard !cleaned.isEmpty else {
            return fallbackSeries.isEmpty ? "New Video" : "\(fallbackSeries) Video"
        }

        return titleCase(cleaned)
    }

    /// A hook can be a full title with emoji and pipes. That reads fine above a
    /// video and terribly as a tag, so tags get a plain-text version.
    static func tagSafe(_ value: String) -> String {
        let firstClause = value
            .components(separatedBy: CharacterSet(charactersIn: "|—–:"))
            .first ?? value

        let letters = firstClause.unicodeScalars.filter { scalar in
            CharacterSet.alphanumerics.contains(scalar) || scalar == " " || scalar == "'"
        }

        let cleaned = String(String.UnicodeScalarView(letters))
            .replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression)
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased()

        // Beyond about five words a tag stops matching anything people type, and
        // a bare number is left over from an export stamp rather than typed.
        let words = cleaned
            .split(separator: " ")
            .filter { !$0.allSatisfy(\.isNumber) }
            .prefix(5)

        return words.joined(separator: " ")
    }

    // MARK: - Upload package

    static func writeUploadPackage(
        videoURL: URL,
        metadata: YouTubeMetadata,
        thumbnailURL: URL?
    ) throws -> URL {
        let packageFolder = videoURL.deletingLastPathComponent().appendingPathComponent(
            uploadFolderName,
            isDirectory: true
        )

        try FileManager.default.createDirectory(
            at: packageFolder,
            withIntermediateDirectories: true
        )

        let baseName = safeFilename(from: metadata.title)

        let readme = """
        YOUTUBE UPLOAD PACKAGE
        \(metadata.title)

        1. Upload your video to YouTube Studio.
        2. Paste the title from \(baseName)_title.txt
        3. Paste the description from \(baseName)_description.txt
        4. Paste the tags from \(baseName)_tags.txt
        5. Upload \(baseName)_thumbnail.jpg as the custom thumbnail.

        Thumbnail text: \(metadata.thumbnailText)
        Title length: \(metadata.title.count) characters
        Tag budget used: \(metadata.tagsLine.count)/\(tagCharacterLimit) characters
        """

        try readme.write(
            to: packageFolder.appendingPathComponent("README_upload_steps.txt"),
            atomically: true,
            encoding: .utf8
        )

        try metadata.title.write(
            to: packageFolder.appendingPathComponent("\(baseName)_title.txt"),
            atomically: true,
            encoding: .utf8
        )

        try metadata.description.write(
            to: packageFolder.appendingPathComponent("\(baseName)_description.txt"),
            atomically: true,
            encoding: .utf8
        )

        try metadata.tagsLine.write(
            to: packageFolder.appendingPathComponent("\(baseName)_tags.txt"),
            atomically: true,
            encoding: .utf8
        )

        if let thumbnailURL,
           FileManager.default.fileExists(atPath: thumbnailURL.path) {
            let destination = packageFolder.appendingPathComponent(thumbnailFilename(for: metadata.title))

            // The generated thumbnail already lives in this folder. Copying onto
            // itself would delete the only copy.
            if thumbnailURL.standardizedFileURL != destination.standardizedFileURL {
                if FileManager.default.fileExists(atPath: destination.path) {
                    try FileManager.default.removeItem(at: destination)
                }
                try FileManager.default.copyItem(at: thumbnailURL, to: destination)
            }
        }

        return packageFolder
    }

    static func thumbnailFilename(for title: String) -> String {
        "\(safeFilename(from: title))_thumbnail.jpg"
    }

    static func packageBaseName(from title: String) -> String {
        safeFilename(from: title)
    }

    // MARK: - Copy building blocks

    /// Combines stores heard in the audio with any the user typed in, keeping
    /// the user's spelling when both refer to the same place.
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

    /// "A", "A and B", or "A, B, and C".
    private static func sentenceList(_ items: [String]) -> String {
        switch items.count {
        case 0:
            return ""
        case 1:
            return items[0]
        case 2:
            return "\(items[0]) and \(items[1])"
        default:
            return items.dropLast().joined(separator: ", ") + ", and \(items[items.count - 1])"
        }
    }

    private static func searchSnippet(
        hook: String,
        preset: BrandPreset,
        places: [String],
        topics: [String],
        transcript: Transcript?
    ) -> String {
        let atStores = places.isEmpty
            ? ""
            : " at \(sentenceList(Array(places.prefix(2))))"

        let snippet: String
        switch preset {
        case .halloweenHunt:
            snippet = "\(hook) — Halloween decorations are already out\(atStores), and these are the finds worth the drive."
        case .storeWalk:
            snippet = "\(hook) — walking the aisles\(atStores) to see what is actually on the shelves right now."
        case .productReview:
            snippet = "\(hook) — an honest, hands-on look before you spend your money."
        case .behindTheScenes:
            snippet = "\(hook) — a behind-the-scenes look at how this one came together."
        case .custom:
            if looksLikeTravelStory(hook: hook, places: places, topics: topics, transcript: transcript) {
                let whereAt = places.isEmpty ? "" : " at \(sentenceList(Array(places.prefix(2))))"
                snippet = "\(hook) — ground delays\(whereAt) turned this business trip upside down."
            } else if !topics.isEmpty {
                let focus = sentenceList(Array(topics.prefix(2)).map { $0.lowercased() })
                snippet = "\(hook) — \(focus), and the rest of the story from this shoot."
            } else {
                snippet = "\(hook) — the full story from this shoot."
            }
        }

        guard snippet.count > descriptionSnippetLimit else {
            return snippet
        }

        return String(snippet.prefix(descriptionSnippetLimit - 1)).trimmingCharacters(in: .whitespaces) + "…"
    }

    /// Built from the stores and subjects found in the video rather than from
    /// the title, so the description describes the content instead of restating
    /// the name of the upload.
    private static func bodyCopy(
        preset: BrandPreset,
        places: [String],
        topics: [String],
        transcript: Transcript?
    ) -> String {
        if preset == .custom,
           looksLikeTravelStory(hook: "", places: places, topics: topics, transcript: transcript) {
            var sentences: [String] = [
                "This one is about the travel day going sideways — not a store walk."
            ]
            if !places.isEmpty {
                sentences.append("We were dealing with chaos around \(sentenceList(places)).")
            }
            if transcriptMentions(transcript, anyOf: ["missed", "miss my", "missed my"]) {
                sentences.append("The delays cost me the business trip.")
            } else if transcriptMentions(transcript, anyOf: ["delay", "delayed", "ground"]) {
                sentences.append("Nationwide ground delays wrecked the schedule.")
            }
            if !topics.isEmpty {
                let focus = sentenceList(topics.prefix(4).map { $0.lowercased() })
                sentences.append("Along the way: \(focus).")
            }
            sentences.append("Watch through for how the day actually unfolded.")
            return sentences.joined(separator: " ")
        }

        var sentences: [String] = [openingLine(for: preset)]

        if !places.isEmpty {
            sentences.append("We stopped at \(sentenceList(places)) on this one.")
        }

        if !topics.isEmpty {
            let found = sentenceList(topics.prefix(5).map { $0.lowercased() })
            if preset == .custom {
                sentences.append("This video covers \(found).")
            } else {
                sentences.append("Along the way we found \(found).")
            }
        }

        sentences.append(closingLine(for: preset))

        return sentences.joined(separator: " ")
    }

    private static func openingLine(for preset: BrandPreset) -> String {
        switch preset {
        case .halloweenHunt:
            return "Halloween is creeping into the stores early this year, so we went looking for the good stuff."
        case .storeWalk:
            return "A full walk through the aisles to see what actually made it onto the shelves."
        case .productReview:
            return "A hands-on look after real use — no script, no sponsorship."
        case .behindTheScenes:
            return "A look at how this one actually got made."
        case .custom:
            return "Here is what actually happened in this video."
        }
    }

    private static func closingLine(for preset: BrandPreset) -> String {
        switch preset {
        case .halloweenHunt:
            return "If you are shopping for Halloween this year, this shows what is on the shelves right now, what is worth the price, and what to skip."
        case .storeWalk:
            return "If you want to know what is in stock before you make the trip, this covers it."
        case .productReview:
            return "Stay to the end for whether it is actually worth buying."
        case .behindTheScenes:
            return "Comment if you want a closer look at any part of the setup."
        case .custom:
            return "Watch through for how the day actually unfolded."
        }
    }

    private static func callToAction(channel: String, domain: StoryDomain) -> String {
        let name = channel.isEmpty ? "the channel" : channel

        switch domain {
        case .travelDelay:
            return "Subscribe to \(name) for more travel days — and tell me your worst delay story in the comments."
        case .retailHunt:
            return "Subscribe to \(name) for more store finds, and comment which store you want checked next."
        case .cooking:
            return "Subscribe to \(name) for more kitchen videos, and comment what you want cooked next."
        case .motorsport:
            return "Subscribe to \(name) for more race-day videos, and comment what track you want next."
        case .adventure:
            return "Subscribe to \(name) for more adventures, and comment what you want to see next."
        case .themePark:
            return "Subscribe to \(name) for more park days, and comment your favorite ride."
        case .cruise:
            return "Subscribe to \(name) for more cruise videos, and comment where we should sail next."
        case .family, .general:
            return "Subscribe to \(name) for more real-life adventures, and let me know in the comments what you want to see next."
        }
    }

    private static func hashtagLine(
        series: String,
        preset: BrandPreset,
        hook: String = "",
        places: [String] = [],
        topics: [String] = []
    ) -> String {
        var tags: [String] = []

        func append(_ value: String) {
            let compact = value
                .components(separatedBy: CharacterSet.alphanumerics.inverted)
                .joined()

            guard compact.count >= 3 else { return }

            let tag = "#\(compact.lowercased())"
            guard !tags.contains(tag) else { return }

            tags.append(tag)
        }

        switch preset {
        case .halloweenHunt:
            append("halloween")
            append("halloweenhunt")
        case .storeWalk:
            append("storewalk")
            append("shopwithme")
        case .productReview:
            append("review")
            append("honestreview")
        case .behindTheScenes:
            append("behindthescenes")
            append("bts")
        case .custom:
            if looksLikeTravelStory(hook: hook, places: places, topics: topics, transcript: nil) {
                append("flightdelay")
                append("travelvlog")
                for place in places.prefix(2) {
                    append(place)
                }
            } else {
                for topic in topics.prefix(2) {
                    append(topic)
                }
                for word in hook.split(separator: " ").prefix(2) {
                    append(String(word))
                }
            }
            if tags.isEmpty {
                append("vlog")
            }
        }

        if !series.isEmpty,
           series.lowercased() != "processed",
           series.lowercased() != "custom" {
            append(series)
        }

        // YouTube only surfaces the first three hashtags above the title.
        return tags.prefix(3).joined(separator: " ")
    }

    /// The word viewers pair with a store name when searching this kind of video.
    private static func presetKeyword(_ preset: BrandPreset) -> String {
        switch preset {
        case .halloweenHunt:
            return "halloween"
        case .storeWalk:
            return "shopping"
        case .productReview:
            return "review"
        case .behindTheScenes:
            return "behind the scenes"
        case .custom:
            return "vlog"
        }
    }

    private static func isRetailPreset(_ preset: BrandPreset) -> Bool {
        switch preset {
        case .halloweenHunt, .storeWalk, .productReview:
            return true
        case .behindTheScenes, .custom:
            return false
        }
    }

    private static func looksLikeTravelStory(
        hook: String,
        places: [String],
        topics: [String],
        transcript: Transcript?
    ) -> Bool {
        let haystack = (
            [hook]
                + places
                + topics
                + [transcript?.fullText ?? ""]
        )
            .joined(separator: " ")
            .lowercased()

        let signals = [
            "delay", "delayed", "delays", "flight", "airport", "airline",
            "dfw", "gate", "missed", "boarding", "canceled", "cancelled",
            "layover", "terminal", "ground stop", "baggage", "omaha", "austin"
        ]

        return signals.contains { haystack.contains($0) }
    }

    private static func transcriptMentions(_ transcript: Transcript?, anyOf needles: [String]) -> Bool {
        guard let text = transcript?.fullText.lowercased(), !text.isEmpty else {
            return false
        }
        return needles.contains { text.contains($0) }
    }

    /// Prefer a story-shaped hook from the transcript over the first eight
    /// mumbled words (which often dump a brand name with no payoff).
    static func storyHookSuggestion(
        from transcript: Transcript,
        fallbackURL: URL?,
        fallbackSeries: String,
        brand: BrandSettingsValues
    ) -> String {
        let brief = StoryBriefService.build(
            from: transcript,
            hook: "",
            brand: brand
        )

        // Headline without trailing period for title use.
        let headline = brief.headline
            .trimmingCharacters(in: CharacterSet(charactersIn: "."))
        if headline.count >= 12, headline.count <= 70 {
            return headline
        }

        if !brief.thumbnailText.isEmpty {
            return titleCase(brief.thumbnailText.lowercased())
        }

        if let fallbackURL {
            return hookSuggestion(from: fallbackURL, fallbackSeries: fallbackSeries)
        }

        return fallbackSeries.isEmpty ? "New Video" : "\(fallbackSeries) Video"
    }

    private static func presetTags(_ preset: BrandPreset) -> [String] {
        switch preset {
        case .halloweenHunt:
            return [
                "halloween store hunt",
                "halloween decorations 2026",
                "spooky season shopping",
                "halloween animatronics",
                "seasonal store walkthrough",
                "halloween haul"
            ]
        case .storeWalk:
            return [
                "store walk through",
                "shop with me",
                "new arrivals in stores",
                "retail walkthrough",
                "shelf finds",
                "clearance finds"
            ]
        case .productReview:
            return [
                "honest product review",
                "hands on review",
                "is it worth it",
                "first impressions review",
                "buy or skip"
            ]
        case .behindTheScenes:
            return [
                "behind the scenes",
                "creator workflow",
                "video editing setup",
                "how i film",
                "youtube creator tips"
            ]
        case .custom:
            // Nothing generic is worth spending tag budget on here. The hook and
            // the transcript carry this preset instead.
            return []
        }
    }

    private static func titleCase(_ value: String) -> String {
        let lowercaseWords: Set<String> = [
            "a", "an", "the", "and", "or", "of", "in", "on",
            "at", "to", "for", "with", "vs"
        ]

        let words = value
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .split(separator: " ")

        return words.enumerated().map { index, word in
            let lower = word.lowercased()

            if index > 0, lowercaseWords.contains(lower) {
                return lower
            }

            return lower.prefix(1).uppercased() + lower.dropFirst()
        }
        .joined(separator: " ")
    }

    private static func safeFilename(from title: String) -> String {
        let invalid = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "-_")).inverted
        let cleaned = title
            .components(separatedBy: invalid)
            .filter { !$0.isEmpty }
            .joined(separator: "_")

        return cleaned.isEmpty ? "youtube_upload" : String(cleaned.prefix(80))
    }
}
