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
                    Never invent dialogue or speaker labels.
                    """
                )

                let response = try await session.respond(
                    to: """
                    This is transcript section \(index + 1) of \(transcriptSections.count).
                    Extract only supported story events, location roles, goals,
                    obstacles, outcomes, people, and visual moments. Keep timestamp
                    evidence. Do not write YouTube copy yet. Stay under 120 words.

                    Stable channel context (identity/spelling only; it is not proof
                    that someone participated in this video):
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
                outcomes, people, or causal relationships. A destination is not the
                place where a delay happened. Titles must be grammatical and
                specific, never generic clickbait such as “Is HERE” or “Don't Skip
                This.” Thumbnail text is 2–4 words. Chapters follow actual events.
                """
            )

            let response = try await finalSession.respond(
                to: """
                Build a structured story analysis from these factual transcript
                section summaries.

                Existing filename/hook (may be stale; use only if supported):
                \(existingHook)

                Stable channel context (use for identity, pet type, and correct
                spelling only; never use it as evidence that someone traveled):
                \(brand.channelContext)

                Section summaries:
                \(finalSummaries.enumerated().map { "SECTION \($0.offset + 1):\n\($0.element)" }.joined(separator: "\n\n"))

                Requirements:
                - Identify subject, goal, obstacle, origin, problem location,
                  destination, and outcome separately.
                - Evidence must be a verbatim transcript excerpt with its real
                  timestamp. Never write reconstructed dialogue or speaker labels.
                - Name a traveler only when the transcript explicitly says that
                  person is joining/taking the trip. A person or pet mentioned as
                  emotional support, at home, or in a car is not a traveler.
                - Confidence is 0–100 based on transcript support.
                - Give 4–6 visual targets that could be seen in this video.
                - Give 3–5 factual title ideas.
                - Give 3–5 thumbnail text ideas, each 2–4 words.
                - Give useful event chapters with timestamps in seconds.
                - Give complete searchable tag phrases; never truncate a phrase.
                - Give no more than 3 hashtags.
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

        return StoryAnalysis(
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

        return result
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
