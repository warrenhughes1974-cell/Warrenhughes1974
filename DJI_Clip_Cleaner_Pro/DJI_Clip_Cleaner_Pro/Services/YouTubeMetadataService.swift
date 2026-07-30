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
    static func thumbnailText(from hook: String) -> String {
        let filler: Set<String> = [
            "a", "an", "the", "and", "or", "of", "in", "on", "at",
            "to", "for", "with", "my", "our", "this", "that", "is", "was"
        ]

        let words = hook
            .split(whereSeparator: { $0 == " " || $0 == "·" || $0 == "|" })
            .map { String($0).trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }

        guard !words.isEmpty else { return "" }

        let meaningful = words.filter { !filler.contains($0.lowercased()) }
        let chosen = meaningful.isEmpty ? words : meaningful

        return chosen
            .prefix(maxThumbnailWords)
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
        transcript: Transcript? = nil
    ) -> String {
        let channel = brand.channelPrefix.trimmingCharacters(in: .whitespacesAndNewlines)
        let series = brand.seriesName.trimmingCharacters(in: .whitespacesAndNewlines)
        let cleanHook = titleCase(hook)

        var lines: [String] = []

        // First 150 characters become the search snippet, so lead with the
        // keyword instead of repeating the title verbatim.
        lines.append(searchSnippet(hook: cleanHook, series: series, preset: preset))
        lines.append("")

        if let transcript, !transcript.isEmpty {
            lines.append(transcriptBody(from: transcript, hook: cleanHook))
        } else {
            lines.append(bodyCopy(hook: cleanHook, series: series, preset: preset))
        }

        lines.append("")
        lines.append("CHAPTERS")

        let chapters = transcript.map { TranscriptionService.chapters(from: $0) } ?? []
        if chapters.count > 1 {
            for chapter in chapters {
                lines.append(chapter.formattedLine)
            }
        } else {
            lines.append("0:00 Intro")
            lines.append("(add your timestamps here — YouTube turns these into chapters)")
        }

        lines.append("")
        lines.append(callToAction(for: preset, channel: channel))
        lines.append("")

        if !series.isEmpty {
            lines.append("MORE FROM THIS SERIES")
            lines.append("Watch the full \(series) playlist on the channel.")
            lines.append("")
        }

        lines.append("GEAR & WORKFLOW")
        lines.append("Filmed on DJI · Edited in Filmora")
        lines.append("")
        lines.append(hashtagLine(series: series, preset: preset))

        return lines.joined(separator: "\n")
    }

    private static func transcriptBody(from transcript: Transcript, hook: String) -> String {
        let words = transcript.fullText
            .split(separator: " ")
            .prefix(70)
            .joined(separator: " ")

        let clipped = words.count < transcript.fullText.count ? "\(words)…" : words

        return """
        In this video I cover \(hook.lowercased()).

        \(clipped)

        Full walkthrough below — timestamps jump you to each section.
        """
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
        transcript: Transcript? = nil
    ) -> [String] {
        let cleanHook = hook.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let series = brand.seriesName.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let channel = brand.channelPrefix.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()

        var tags: [String] = []

        // `allowSingleWord` exists only for the exact-match hook. Every other
        // tag must be a phrase, because bare single words are too broad to rank.
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

        // Exact match first — this is the highest-weighted slot.
        append(cleanHook, allowSingleWord: true)

        if !series.isEmpty {
            append("\(cleanHook) \(series)")
            append(series)
        }

        for phrase in transcriptPhrases(from: transcript) {
            append(phrase)
        }

        for tag in presetTags(preset) {
            append(tag)
        }

        if !channel.isEmpty {
            append("\(channel) \(series.isEmpty ? "channel" : series)")
        }

        return Array(tags.prefix(15))
    }

    /// Pulls the most repeated meaningful two-word phrases from what was said.
    private static func transcriptPhrases(from transcript: Transcript?) -> [String] {
        guard let transcript, !transcript.isEmpty else { return [] }

        let filler: Set<String> = [
            "a", "an", "the", "and", "or", "of", "in", "on", "at", "to",
            "for", "with", "so", "uh", "um", "like", "just", "you", "i",
            "we", "this", "that", "it", "is", "are", "was", "were", "my",
            "me", "be", "do", "did", "have", "has", "had", "but", "if"
        ]

        let words = transcript.fullText
            .lowercased()
            .components(separatedBy: CharacterSet.alphanumerics.inverted)
            .filter { !$0.isEmpty && !filler.contains($0) && $0.count > 2 }

        guard words.count >= 2 else { return [] }

        var counts: [String: Int] = [:]

        for index in 0..<(words.count - 1) {
            let phrase = "\(words[index]) \(words[index + 1])"
            counts[phrase, default: 0] += 1
        }

        return counts
            .sorted { lhs, rhs in
                if lhs.value == rhs.value {
                    return lhs.key < rhs.key
                }
                return lhs.value > rhs.value
            }
            .prefix(6)
            .map(\.key)
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

    static func hookSuggestion(from videoURL: URL, fallbackSeries: String = "") -> String {
        let baseName = videoURL.deletingPathExtension().lastPathComponent
        let cleaned = baseName
            .replacingOccurrences(of: "_", with: " ")
            .replacingOccurrences(of: "-", with: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)

        guard !cleaned.isEmpty else {
            return fallbackSeries.isEmpty ? "New Video" : "\(fallbackSeries) Video"
        }

        return titleCase(cleaned)
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

    private static func searchSnippet(
        hook: String,
        series: String,
        preset: BrandPreset
    ) -> String {
        let context = series.isEmpty ? "" : " \(series.lowercased())"

        let snippet: String
        switch preset {
        case .halloweenHunt:
            snippet = "\(hook) — hunting Halloween decorations and spooky store finds in this\(context)."
        case .storeWalk:
            snippet = "\(hook) — walking the aisles to find what's new on the shelves in this\(context)."
        case .productReview:
            snippet = "\(hook) — an honest, hands-on look before you spend your money."
        case .behindTheScenes:
            snippet = "\(hook) — a behind-the-scenes look at how this\(context) came together."
        case .custom:
            snippet = "\(hook) — everything worth seeing in this\(context)."
        }

        guard snippet.count > descriptionSnippetLimit else {
            return snippet
        }

        return String(snippet.prefix(descriptionSnippetLimit - 1)).trimmingCharacters(in: .whitespaces) + "…"
    }

    private static func bodyCopy(
        hook: String,
        series: String,
        preset: BrandPreset
    ) -> String {
        let seriesLabel = series.isEmpty ? "video" : series

        switch preset {
        case .halloweenHunt:
            return """
            In this \(seriesLabel) we go looking for \(hook). Expect animatronics, seasonal displays, \
            and the kind of Halloween decorations that are worth driving across town for.

            If you are shopping for Halloween this year, this walkthrough shows what is actually on \
            the shelves right now, what is worth the price, and what to skip.
            """
        case .storeWalk:
            return """
            This \(seriesLabel) is a full walk through the aisles looking at \(hook). \
            New arrivals, clearance finds, and anything that stood out on the shelf.

            If you want to see what is in stock before you make the trip, this walkthrough covers it.
            """
        case .productReview:
            return """
            A hands-on look at \(hook). What it does well, where it falls short, and whether it is \
            worth the money.

            No sponsorship and no script — just an honest review after real use.
            """
        case .behindTheScenes:
            return """
            A behind-the-scenes look at \(hook). The setup, the gear, and how this \(seriesLabel) \
            actually gets made.
            """
        case .custom:
            return """
            This \(seriesLabel) covers \(hook). Watch through for the full walkthrough.
            """
        }
    }

    private static func callToAction(for preset: BrandPreset, channel: String) -> String {
        let name = channel.isEmpty ? "the channel" : channel

        switch preset {
        case .halloweenHunt:
            return "Subscribe to \(name) for more Halloween hunts, and tell me in the comments which find you would take home."
        case .storeWalk:
            return "Subscribe to \(name) for more store walks, and comment which store you want me to check next."
        case .productReview:
            return "Subscribe to \(name) for more honest reviews, and comment what you want reviewed next."
        case .behindTheScenes:
            return "Subscribe to \(name) for more behind-the-scenes videos, and comment what you want to see next."
        case .custom:
            return "Subscribe to \(name) for more videos, and let me know in the comments what you want to see next."
        }
    }

    private static func hashtagLine(
        series: String,
        preset: BrandPreset
    ) -> String {
        var tags: [String] = []

        func append(_ value: String) {
            let compact = value
                .components(separatedBy: CharacterSet.alphanumerics.inverted)
                .joined()

            guard !compact.isEmpty else { return }

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
            append("vlog")
        }

        if !series.isEmpty {
            append(series)
        }

        // YouTube only surfaces the first three hashtags above the title.
        return tags.prefix(3).joined(separator: " ")
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
            return [
                "day in the life",
                "vlog channel",
                "new video upload"
            ]
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
