import Foundation

#if canImport(FoundationModels)
import FoundationModels
#endif

enum StoryAnalysisSource: String, Sendable {
    case appleIntelligence = "Apple Intelligence (On Device)"
    case deterministicFallback = "Local Fallback — Review Required"
}

struct StoryChapterCandidate: Sendable, Equatable {
    var startTime: TimeInterval
    var title: String
}

struct StoryAnalysis: Sendable, Equatable {
    var domain: StoryDomain
    var subject: String
    var goal: String
    var obstacle: String
    var origin: String
    var problemLocation: String
    var destination: String
    var outcome: String
    var summary: String
    var evidence: [String]
    var confidence: Int
    var visualTargets: [String]
    var titleIdeas: [String]
    var thumbnailTextIdeas: [String]
    var chapters: [StoryChapterCandidate]
    var tags: [String]
    var hashtags: [String]
    var source: StoryAnalysisSource
}

enum OnDeviceStoryModelAvailability: Sendable, Equatable {
    case available
    case unavailable(String)

    var message: String {
        switch self {
        case .available:
            return "Apple Intelligence is ready. Story analysis stays on this Mac."
        case .unavailable(let reason):
            return "Apple Intelligence unavailable: \(reason)"
        }
    }
}

enum OnDeviceStoryAnalysisService {
    enum ServiceError: LocalizedError {
        case modelUnavailable(String)
        case emptyTranscript

        var errorDescription: String? {
            switch self {
            case .modelUnavailable(let reason):
                return "On-device story analysis is unavailable: \(reason)"
            case .emptyTranscript:
                return "The transcript is empty, so there is no story to analyze."
            }
        }
    }

    static var availability: OnDeviceStoryModelAvailability {
        #if canImport(FoundationModels)
        if #available(macOS 26.0, *) {
            switch SystemLanguageModel.default.availability {
            case .available:
                return .available
            case .unavailable(let reason):
                return .unavailable(String(describing: reason))
            @unknown default:
                return .unavailable("Unknown model state")
            }
        }
        #endif

        return .unavailable("Requires macOS 26 with Apple Intelligence enabled")
    }

    static func analyze(
        transcript: Transcript,
        existingHook: String,
        brand: BrandSettingsValues
    ) async throws -> StoryAnalysis {
        guard !transcript.isEmpty else {
            throw ServiceError.emptyTranscript
        }

        #if canImport(FoundationModels)
        if #available(macOS 26.0, *) {
            guard case .available = SystemLanguageModel.default.availability else {
                throw ServiceError.modelUnavailable(availability.message)
            }

            let transcriptSections = timedTranscriptSections(transcript)
            var sectionSummaries: [String] = []

            // Keep each request inside the on-device model's context window.
            for (index, section) in transcriptSections.enumerated() {
                let session = LanguageModelSession(
                    instructions: """
                    Analyze video transcripts factually. Never infer that a person
                    was in a location merely because it was mentioned. Distinguish
                    origin, destination, problem location, goal, obstacle, and
                    outcome. Preserve timestamps and explicitly mark unknown facts.
                    Never invent dialogue or speaker labels. Prefer empty/unknown
                    over any guess. Channel identity notes are spelling only.
                    """
                )

                let response = try await session.respond(
                    to: """
                    This is transcript section \(index + 1) of \(transcriptSections.count).
                    Extract only supported story events, location roles, goals,
                    obstacles, outcomes, people, and visual moments. Keep timestamp
                    evidence. Do not write YouTube copy yet. Stay under 120 words.
                    If a fact is not explicit in this section, omit it.

                    Stable channel context (identity/spelling only; it is not proof
                    that someone participated in this video, traveled, or is on camera):
                    \(brand.channelContext)

                    \(section)
                    """
                )
                sectionSummaries.append(response.content)
            }

            // Long videos may produce many section summaries. Condense in
            // factual batches instead of silently dropping the ending.
            var finalSummaries = sectionSummaries
            // Foundation Models shares a 4,096-token window between prompt,
            // generated schema, and response. Keep final factual notes compact.
            while finalSummaries.joined(separator: "\n\n").count > 7_000 {
                var condensed: [String] = []
                for start in stride(from: 0, to: finalSummaries.count, by: 4) {
                    let end = min(start + 4, finalSummaries.count)
                    let batch = finalSummaries[start..<end].joined(separator: "\n\n")
                    let session = LanguageModelSession(
                        instructions: """
                        Condense factual transcript notes without dropping goals,
                        obstacles, location roles, outcomes, or timestamps. Do not
                        infer anything new. Stay under 250 words.
                        """
                    )
                    let response = try await session.respond(to: batch)
                    condensed.append(response.content)
                }
                finalSummaries = condensed
            }

            let finalSession = LanguageModelSession(
                instructions: """
                You are a factual story editor for a reusable video-preparation app.
                Produce natural American English. Use only supplied transcript
                evidence. Empty string means unknown. Do not invent location roles,
                outcomes, people, themes, or causal relationships. Do not assume a
                family trip, family vlog, or pet travel theme. A destination is not
                the place where a delay happened. Titles must be grammatical and
                specific, never generic clickbait such as “Is HERE” or “Don't Skip
                This.” Thumbnail text is 2–4 words. Chapters follow actual events.
                Tags and hashtags must come from words actually spoken.
                """
            )

            let response = try await finalSession.respond(
                to: """
                Build a structured story analysis from these factual transcript
                section summaries.

                Existing filename/hook (may be stale; use only if supported):
                \(existingHook)

                Stable channel context (use for identity, pet type, and correct
                spelling only; never as evidence that someone traveled, appeared,
                or that this is a family/lifestyle video):
                \(brand.channelContext)

                Section summaries:
                \(finalSummaries.enumerated().map { "SECTION \($0.offset + 1):\n\($0.element)" }.joined(separator: "\n\n"))

                Requirements:
                - Identify subject, goal, obstacle, origin, problem location,
                  destination, and outcome separately. Leave unknown fields empty.
                - Evidence must be a verbatim transcript excerpt with its real
                  timestamp. Never write reconstructed dialogue or speaker labels.
                - Name a person only when the transcript explicitly places them in
                  this video's events. Pets/family named only as support are not
                  cast members or travelers.
                - Do not choose a family domain unless the transcript clearly shows
                  a family or pet lifestyle story.
                - Confidence is 0–100 based on transcript support.
                - Give 4–6 visual targets grounded in spoken content.
                - Give 3–5 factual title ideas using spoken facts only.
                - Give 3–5 thumbnail text ideas, each 2–4 words.
                - Give useful event chapters with timestamps in seconds.
                - Tags must be complete phrases supported by spoken words.
                - Hashtags (max 3) must compact spoken topics only — never invent
                  #FamilyTravel / #FamilyVlog without those words being earned.
                """,
                generating: GeneratedStoryAnalysis.self
            )

            return validated(
                response.content.storyAnalysis,
                against: transcript
            )
        }
        #endif

        throw ServiceError.modelUnavailable(availability.message)
    }

    /// Safe local draft when Apple Intelligence is temporarily unavailable.
    /// It is never auto-confirmed; the user must review every relationship.
    static func fallback(
        transcript: Transcript,
        hook: String,
        brand: BrandSettingsValues
    ) -> StoryAnalysis {
        let brief = StoryBriefService.build(
            from: transcript,
            hook: hook,
            brand: brand
        )

        let draft = StoryAnalysis(
            domain: brief.domain,
            subject: brief.headline,
            goal: "",
            obstacle: brief.beats.first ?? "",
            origin: "",
            // Places were detected, but their semantic roles are unknown.
            // Never guess problem location vs destination in fallback mode.
            problemLocation: "",
            destination: "",
            outcome: "",
            summary: brief.summary,
            evidence: [],
            confidence: 25,
            visualTargets: brief.visualTargets,
            titleIdeas: [brief.headline],
            thumbnailTextIdeas: [brief.thumbnailText],
            chapters: brief.chapters.map {
                StoryChapterCandidate(startTime: $0.startTime, title: $0.title)
            },
            tags: brief.tags,
            hashtags: brief.hashtags,
            source: .deterministicFallback
        )
        return validated(draft, against: transcript)
    }

    // MARK: - Transcript preparation

    private static func timedTranscriptSections(_ transcript: Transcript) -> [String] {
        let duration = transcript.segments.last?.endTime ?? 0
        // Fine-grained windows give the model real evidence/chapter timestamps
        // instead of one coarse timestamp for a 90-second block.
        let window: TimeInterval = 20
        var lines: [String] = []
        var start: TimeInterval = 0

        while start <= duration {
            let text = transcript.text(overlapping: start, duration: window)
            if !text.isEmpty {
                lines.append("[\(TranscriptChapter.timecode(start))] \(text)")
            }
            start += window
        }

        guard !lines.isEmpty else {
            return [transcript.fullText]
        }

        let maximumCharacters = 8_000
        var sections: [String] = []
        var current: [String] = []
        var currentCount = 0

        for line in lines {
            if !current.isEmpty, currentCount + line.count > maximumCharacters {
                sections.append(current.joined(separator: "\n"))
                current = []
                currentCount = 0
            }
            current.append(line)
            currentCount += line.count + 1
        }

        if !current.isEmpty {
            sections.append(current.joined(separator: "\n"))
        }

        return sections
    }

    private static func validated(
        _ proposed: StoryAnalysis,
        against transcript: Transcript
    ) -> StoryAnalysis {
        var result = proposed
        let transcriptText = normalized(transcript.fullText)
        let transcriptBag = " \(transcriptText) "
        var clearedUnsupportedField = false

        result.evidence = proposed.evidence.filter {
            evidenceIsSupported(
                $0,
                transcriptText: transcriptText,
                transcript: transcript
            )
        }

        // Fabricated evidence is a strong signal that all semantic roles need
        // human review. Keep the draft editable, but remove false confidence.
        if result.evidence.isEmpty {
            result.confidence = min(result.confidence, 35)
        } else if result.evidence.count < proposed.evidence.count {
            result.confidence = min(result.confidence, 55)
        }

        let duration = transcript.segments.last?.endTime ?? 0
        result.chapters = proposed.chapters
            .filter {
                $0.startTime >= 0
                    && $0.startTime <= duration
                    && !$0.title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                    && chapterIsSupported($0, transcript: transcript)
            }
            .sorted { $0.startTime < $1.startTime }

        // Reject a fake compressed timeline (for example all chapters in the
        // first 80 seconds of an 11-minute video).
        if duration >= 300,
           (result.chapters.last?.startTime ?? 0) < duration * 0.35 {
            result.chapters = []
            result.confidence = min(result.confidence, 55)
        }

        // Family domain must be earned by spoken lifestyle/family/pet signals.
        if result.domain == .family && !transcriptSupportsFamilySignals(transcriptBag) {
            result.domain = .general
            clearedUnsupportedField = true
        }

        let groundedOrigin = placeRoleOrEmpty(result.origin, in: transcriptBag)
        let groundedProblem = placeRoleOrEmpty(result.problemLocation, in: transcriptBag)
        var groundedDestination = placeRoleOrEmpty(result.destination, in: transcriptBag)
        if groundedOrigin != result.origin
            || groundedProblem != result.problemLocation
            || groundedDestination != result.destination {
            clearedUnsupportedField = true
        }
        if !groundedProblem.isEmpty,
           groundedProblem.caseInsensitiveCompare(groundedDestination) == .orderedSame {
            groundedDestination = ""
            clearedUnsupportedField = true
        }
        result.origin = groundedOrigin
        result.problemLocation = groundedProblem
        result.destination = groundedDestination

        let groundedGoal = groundedPhraseOrEmpty(result.goal, in: transcriptBag, minimumCoverage: 0.5)
        let groundedObstacle = groundedPhraseOrEmpty(result.obstacle, in: transcriptBag, minimumCoverage: 0.5)
        let groundedOutcome = groundedPhraseOrEmpty(result.outcome, in: transcriptBag, minimumCoverage: 0.5)
        var groundedSubject = groundedPhraseOrEmpty(result.subject, in: transcriptBag, minimumCoverage: 0.4)
        if groundedGoal != result.goal
            || groundedObstacle != result.obstacle
            || groundedOutcome != result.outcome
            || groundedSubject != result.subject {
            clearedUnsupportedField = true
        }
        if groundedSubject.isEmpty {
            groundedSubject = TranscriptKeywordService.topics(from: transcript, limit: 1).first
                ?? result.subject.trimmingCharacters(in: .whitespacesAndNewlines)
        }
        result.goal = groundedGoal
        result.obstacle = groundedObstacle
        result.outcome = groundedOutcome
        result.subject = groundedSubject

        let cleanedSummary = groundedSummary(
            result.summary,
            in: transcriptBag,
            subject: result.subject,
            goal: result.goal,
            obstacle: result.obstacle,
            outcome: result.outcome
        )
        if cleanedSummary != result.summary.trimmingCharacters(in: .whitespacesAndNewlines) {
            clearedUnsupportedField = true
        }
        result.summary = cleanedSummary

        result.titleIdeas = result.titleIdeas.compactMap {
            groundedTitleIdea($0, in: transcriptBag)
        }
        if result.titleIdeas.isEmpty, !result.subject.isEmpty {
            result.titleIdeas = [result.subject]
        }

        result.thumbnailTextIdeas = result.thumbnailTextIdeas.compactMap {
            groundedThumbnailIdea($0, in: transcriptBag)
        }
        result.visualTargets = result.visualTargets.filter {
            phraseIsGrounded($0, in: transcriptBag, minimumCoverage: 0.5)
        }

        let groundedTagList = groundedTags(
            result.tags,
            transcript: transcript,
            transcriptBag: transcriptBag
        )
        if groundedTagList != result.tags {
            clearedUnsupportedField = true
        }
        result.tags = groundedTagList
        result.hashtags = groundedHashtags(
            result.hashtags,
            transcriptBag: transcriptBag,
            tags: result.tags
        )

        if clearedUnsupportedField {
            result.confidence = min(result.confidence, 55)
        }

        return result
    }

    // MARK: - Invent-nothing gates

    private static let stopWords: Set<String> = [
        "the", "a", "an", "and", "or", "to", "from", "at", "in", "on", "of",
        "for", "with", "our", "my", "we", "you", "they", "their", "this",
        "that", "was", "were", "are", "is", "be", "been", "as", "by", "into",
        "about", "over", "after", "before", "than", "then", "just", "very",
        "really", "here", "there", "what", "when", "where", "who", "how",
        "not", "no", "yes", "up", "out", "off", "so", "if", "but", "all",
        "get", "got", "getting", "have", "had", "has", "do", "did", "does",
        "will", "would", "could", "should", "can", "cant", "dont", "didnt",
        "im", "ive", "its", "our", "ours", "your", "video", "vlog", "day"
    ]

    private static func contentWords(_ value: String) -> [String] {
        normalized(value)
            .split(separator: " ")
            .map(String.init)
            .filter { $0.count >= 3 && !stopWords.contains($0) }
    }

    private static func transcriptContainsWord(_ word: String, in transcriptBag: String) -> Bool {
        transcriptBag.contains(" \(word) ")
    }

    private static func phraseIsGrounded(
        _ phrase: String,
        in transcriptBag: String,
        minimumCoverage: Double
    ) -> Bool {
        let words = contentWords(phrase)
        guard !words.isEmpty else { return false }
        let hits = words.filter { transcriptContainsWord($0, in: transcriptBag) }.count
        return Double(hits) / Double(words.count) >= minimumCoverage
    }

    private static func groundedPhraseOrEmpty(
        _ value: String,
        in transcriptBag: String,
        minimumCoverage: Double
    ) -> String {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return "" }
        guard !looksLikeInventedDialogue(trimmed) else { return "" }
        return phraseIsGrounded(trimmed, in: transcriptBag, minimumCoverage: minimumCoverage)
            ? trimmed
            : ""
    }

    private static func placeRoleOrEmpty(_ value: String, in transcriptBag: String) -> String {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return "" }
        let words = contentWords(trimmed)
        // Short place tokens like "dfw" / "omaha" must all appear.
        let tokens = words.isEmpty
            ? normalized(trimmed).split(separator: " ").map(String.init).filter { $0.count >= 2 }
            : words
        guard !tokens.isEmpty else { return "" }
        guard tokens.allSatisfy({ transcriptContainsWord($0, in: transcriptBag) }) else {
            return ""
        }
        return trimmed
    }

    private static func transcriptSupportsFamilySignals(_ transcriptBag: String) -> Bool {
        let signals = [
            "family", "kids", "kid", "daughter", "son", "wife", "husband",
            "mom", "dad", "parent", "parents", "gabie", "domi", "puppy",
            "puppies", "dog", "dogs", "pet", "pets", "coco", "penny",
            "ramsey", "sadie", "alani", "ryder"
        ]
        return signals.contains { transcriptContainsWord($0, in: transcriptBag) }
    }

    private static func looksLikeInventedDialogue(_ value: String) -> Bool {
        let lower = value.lowercased()
        if value.contains("\"") || value.contains("“") || value.contains("”") {
            return true
        }
        if lower.contains(" said ") || lower.contains(" says ") || lower.contains(" asked ") {
            return true
        }
        // "Coco:" / "Warren:" style speaker labels
        if lower.range(of: #"\b[a-z]{2,}:\s"#, options: .regularExpression) != nil {
            return true
        }
        return false
    }

    private static func groundedSummary(
        _ summary: String,
        in transcriptBag: String,
        subject: String,
        goal: String,
        obstacle: String,
        outcome: String
    ) -> String {
        let trimmed = summary.trimmingCharacters(in: .whitespacesAndNewlines)
        let sentences = trimmed
            .components(separatedBy: CharacterSet(charactersIn: ".!?"))
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }

        let kept = sentences.filter { sentence in
            !looksLikeInventedDialogue(sentence)
                && phraseIsGrounded(sentence, in: transcriptBag, minimumCoverage: 0.5)
                && !isUnsupportedThemeSentence(sentence, transcriptBag: transcriptBag)
        }

        if !kept.isEmpty {
            return kept.joined(separator: ". ") + "."
        }

        var parts: [String] = []
        if !subject.isEmpty { parts.append(subject) }
        if !goal.isEmpty { parts.append("Goal: \(goal)") }
        if !obstacle.isEmpty { parts.append("Obstacle: \(obstacle)") }
        if !outcome.isEmpty { parts.append("Outcome: \(outcome)") }
        if parts.isEmpty {
            return "Review the transcript and fill in only facts you can confirm."
        }
        return parts.joined(separator: ". ") + "."
    }

    private static func isUnsupportedThemeSentence(
        _ sentence: String,
        transcriptBag: String
    ) -> Bool {
        let words = Set(contentWords(sentence))
        let familyThemes = ["family", "families"]
        let hasFamilyTheme = familyThemes.contains { words.contains($0) }
        // Saying “family” in the summary requires the word in the transcript.
        // Pet/support mentions are not a license to write a family-trip story.
        if hasFamilyTheme && !transcriptContainsWord("family", in: transcriptBag) {
            return true
        }
        return false
    }

    private static func groundedTitleIdea(_ title: String, in transcriptBag: String) -> String? {
        let trimmed = title.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }
        guard !looksLikeInventedDialogue(trimmed) else { return nil }
        guard !isUnsupportedThemeSentence(trimmed, transcriptBag: transcriptBag) else {
            return nil
        }
        return phraseIsGrounded(trimmed, in: transcriptBag, minimumCoverage: 0.4)
            ? trimmed
            : nil
    }

    private static func groundedThumbnailIdea(_ text: String, in transcriptBag: String) -> String? {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }
        let wordCount = trimmed.split(separator: " ").count
        guard (2...4).contains(wordCount) else { return nil }
        return phraseIsGrounded(trimmed, in: transcriptBag, minimumCoverage: 0.5)
            ? trimmed.uppercased()
            : nil
    }

    private static func groundedTags(
        _ proposed: [String],
        transcript: Transcript,
        transcriptBag: String
    ) -> [String] {
        var tags: [String] = []

        func add(_ raw: String) {
            let cleaned = raw.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !cleaned.isEmpty else { return }
            let key = cleaned.lowercased()
            guard !tags.contains(where: { $0.lowercased() == key }) else { return }
            guard phraseIsGrounded(cleaned, in: transcriptBag, minimumCoverage: 0.67) else { return }
            guard !isUnsupportedThemeTag(cleaned, transcriptBag: transcriptBag) else { return }
            tags.append(cleaned)
        }

        for tag in proposed {
            add(tag)
        }
        for phrase in TranscriptKeywordService.tagPhrases(from: transcript, limit: 8) {
            add(phrase)
        }
        for place in TranscriptKeywordService.places(from: transcript, limit: 4) {
            add(place)
        }

        return Array(tags.prefix(15))
    }

    private static func isUnsupportedThemeTag(_ tag: String, transcriptBag: String) -> Bool {
        let compact = tag
            .lowercased()
            .components(separatedBy: CharacterSet.alphanumerics.inverted)
            .joined()
        // Pet mentions alone must not unlock #FamilyTravel / #FamilyVlog.
        let familyCompacts = ["family", "familyvlog", "familytravel", "familytrip", "familylife"]
        if familyCompacts.contains(where: { compact.contains($0) }) {
            return !transcriptContainsWord("family", in: transcriptBag)
        }
        return false
    }

    private static func groundedHashtags(
        _ proposed: [String],
        transcriptBag: String,
        tags: [String]
    ) -> [String] {
        var hashtags: [String] = []

        func addCompact(_ body: String) {
            let compact = body
                .lowercased()
                .components(separatedBy: CharacterSet.alphanumerics.inverted)
                .joined()
            guard compact.count >= 3 else { return }
            let tag = "#\(compact)"
            guard !hashtags.contains(tag) else { return }
            guard hashtagBodyIsSupported(compact, transcriptBag: transcriptBag, tags: tags) else {
                return
            }
            hashtags.append(tag)
        }

        for raw in proposed {
            let body = raw.hasPrefix("#") ? String(raw.dropFirst()) : raw
            addCompact(body)
        }
        for tag in tags.prefix(5) {
            addCompact(tag)
        }

        return Array(hashtags.prefix(3))
    }

    private static func hashtagBodyIsSupported(
        _ body: String,
        transcriptBag: String,
        tags: [String]
    ) -> Bool {
        if isUnsupportedThemeTag(body, transcriptBag: transcriptBag) {
            return false
        }
        if tags.contains(where: {
            $0.lowercased()
                .components(separatedBy: CharacterSet.alphanumerics.inverted)
                .joined() == body
        }) {
            return true
        }
        if transcriptContainsWord(body, in: transcriptBag) {
            return true
        }
        // Accept multi-word spoken support when the hashtag concatenates them.
        let words = contentWords(body)
        if !words.isEmpty,
           words.allSatisfy({ transcriptContainsWord($0, in: transcriptBag) }) {
            return true
        }
        // Common delay compounds earned by spoken delay/airport words.
        let earnedCompounds: [String: [String]] = [
            "flightdelay": ["flight", "delay", "delayed", "delays"],
            "travelvlog": ["travel", "flight", "airport", "trip"],
            "grounddelay": ["ground", "delay", "delayed"],
            "airportdelay": ["airport", "delay", "delayed"]
        ]
        if let needles = earnedCompounds[body] {
            return needles.contains { transcriptContainsWord($0, in: transcriptBag) }
        }
        return false
    }

    private static func evidenceIsSupported(
        _ evidence: String,
        transcriptText: String,
        transcript: Transcript? = nil
    ) -> Bool {
        guard let timestamp = evidenceTimestamp(evidence) else { return false }
        let quote = evidence
            .replacingOccurrences(
                of: #"\[?\d{1,2}:\d{2}(?::\d{2})?\]?"#,
                with: " ",
                options: .regularExpression
            )
        let normalizedQuote = normalized(quote)
        guard normalizedQuote.split(separator: " ").count >= 5 else {
            return false
        }

        guard let transcript else {
            return transcriptText.contains(normalizedQuote)
        }
        let nearby = normalized(
            transcript.text(
                overlapping: max(timestamp - 8, 0),
                duration: 30
            )
        )
        return nearby.contains(normalizedQuote)
    }

    private static func evidenceTimestamp(_ evidence: String) -> TimeInterval? {
        guard let match = evidence.range(
            of: #"\d{1,2}:\d{2}(?::\d{2})?"#,
            options: .regularExpression
        ) else { return nil }

        let parts = evidence[match].split(separator: ":").compactMap { Double($0) }
        if parts.count == 2 {
            return (parts[0] * 60) + parts[1]
        }
        if parts.count == 3 {
            return (parts[0] * 3_600) + (parts[1] * 60) + parts[2]
        }
        return nil
    }

    private static func chapterIsSupported(
        _ chapter: StoryChapterCandidate,
        transcript: Transcript
    ) -> Bool {
        let nearby = normalized(
            transcript.text(
                overlapping: max(chapter.startTime - 12, 0),
                duration: 45
            )
        )
        guard !nearby.isEmpty else { return false }

        let generic: Set<String> = [
            "the", "a", "an", "and", "or", "to", "from", "at", "in",
            "our", "my", "we", "first", "second", "next", "final"
        ]
        let nearbyWords = Set(nearby.split(separator: " ").map(String.init))
        let titleWords = normalized(chapter.title)
            .split(separator: " ")
            .map(String.init)
            .filter { $0.count >= 4 && !generic.contains($0) }

        guard !titleWords.isEmpty else { return false }
        return titleWords.contains { nearbyWords.contains($0) }
    }

    private static func normalized(_ value: String) -> String {
        value
            .lowercased()
            .components(separatedBy: CharacterSet.alphanumerics.inverted)
            .filter { !$0.isEmpty }
            .joined(separator: " ")
    }
}

#if canImport(FoundationModels)
@available(macOS 26.0, *)
@Generable(description: "The broad kind of story in the video")
private enum GeneratedStoryDomain {
    case travelDelay
    case retailHunt
    case cooking
    case motorsport
    case adventure
    case themePark
    case cruise
    case family
    case general

    var storyDomain: StoryDomain {
        switch self {
        case .travelDelay: return .travelDelay
        case .retailHunt: return .retailHunt
        case .cooking: return .cooking
        case .motorsport: return .motorsport
        case .adventure: return .adventure
        case .themePark: return .themePark
        case .cruise: return .cruise
        case .family: return .family
        case .general: return .general
        }
    }
}

@available(macOS 26.0, *)
@Generable(description: "One factual chapter candidate from a video transcript")
private struct GeneratedStoryChapter {
    @Guide(description: "Chapter start time in seconds")
    var startTime: Double

    @Guide(description: "Short factual chapter title")
    var title: String
}

@available(macOS 26.0, *)
@Generable(description: "Structured factual analysis of one video's story")
private struct GeneratedStoryAnalysis {
    var domain: GeneratedStoryDomain

    @Guide(description: "The main subject of the video")
    var subject: String

    @Guide(description: "What the people were trying to do; empty if unknown")
    var goal: String

    @Guide(description: "The main obstacle or conflict; empty if unknown")
    var obstacle: String

    @Guide(description: "Where the journey started; empty if unknown")
    var origin: String

    @Guide(description: "Where the obstacle happened; empty if unknown")
    var problemLocation: String

    @Guide(description: "Where they intended to go; empty if unknown")
    var destination: String

    @Guide(description: "What ultimately happened; empty if unknown")
    var outcome: String

    @Guide(description: "Natural two-to-four sentence story summary")
    var summary: String

    @Guide(description: "Verbatim timestamped transcript excerpts; never reconstructed dialogue or speaker labels")
    var evidence: [String]

    @Guide(description: "Overall factual confidence from 0 through 100")
    var confidence: Int

    @Guide(description: "Visible subjects that would illustrate this exact story")
    var visualTargets: [String]

    @Guide(description: "Three to five factual natural YouTube title ideas")
    var titleIdeas: [String]

    @Guide(description: "Three to five thumbnail phrases, each two to four words")
    var thumbnailTextIdeas: [String]

    @Guide(description: "Event-based chapter candidates")
    var chapters: [GeneratedStoryChapter]

    @Guide(description: "Complete searchable tag phrases")
    var tags: [String]

    @Guide(description: "Up to three hashtags beginning with #")
    var hashtags: [String]

    var storyAnalysis: StoryAnalysis {
        StoryAnalysis(
            domain: domain.storyDomain,
            subject: subject,
            goal: goal,
            obstacle: obstacle,
            origin: origin,
            problemLocation: problemLocation,
            destination: destination,
            outcome: outcome,
            summary: summary,
            evidence: evidence,
            confidence: min(max(confidence, 0), 100),
            visualTargets: visualTargets,
            titleIdeas: titleIdeas,
            thumbnailTextIdeas: thumbnailTextIdeas,
            chapters: chapters.map {
                StoryChapterCandidate(
                    startTime: max($0.startTime, 0),
                    title: $0.title
                )
            },
            tags: tags,
            hashtags: hashtags,
            source: .appleIntelligence
        )
    }
}
#endif
