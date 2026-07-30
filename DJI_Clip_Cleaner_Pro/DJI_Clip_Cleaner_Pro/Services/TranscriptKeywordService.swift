import Foundation
import NaturalLanguage

struct TranscriptKeyword: Sendable, Equatable {
    let phrase: String
    let count: Int
}

/// Turns raw dictation into phrases a person would actually type into YouTube.
///
/// Speech-to-text output is mostly filler. Counting plain word pairs over it
/// produces things like "don know" and "they got", because punctuation is
/// stripped before pairing and non-adjacent words end up glued together. This
/// service tags each word with its part of speech, keeps only phrases anchored
/// on a real noun, and never pairs words that were not actually spoken side by
/// side.
enum TranscriptKeywordService {
    /// Longest a chapter title should get before it stops scanning cleanly.
    private static let maximumTitleLength = 42

    // MARK: - Public

    /// Repeated, noun-anchored phrases suitable for YouTube tags. Single words
    /// are withheld here on purpose — a bare word is too broad to rank.
    static func tagPhrases(from transcript: Transcript?, limit: Int = 8) -> [String] {
        ranked(from: transcript)
            .filter { $0.phrase.contains(" ") }
            .prefix(limit)
            .map(\.phrase)
    }

    /// Subjects covered in the video, formatted for a written description. A
    /// recurring single word is a fine bullet point even though it is a poor tag.
    static func topics(from transcript: Transcript?, limit: Int = 8) -> [String] {
        ranked(from: transcript)
            .prefix(limit)
            .map { titleCase($0.phrase) }
    }

    /// A readable title for one stretch of speech, or nil when that stretch has
    /// nothing worth naming. Callers should skip the chapter rather than fall
    /// back to raw transcript text.
    static func chapterTitle(from text: String) -> String? {
        guard let phrase = bestPhrase(in: tokenize(text)) else { return nil }

        let title = titleCase(phrase)
        return title.count <= maximumTitleLength ? title : nil
    }

    // MARK: - Ranking

    private static func ranked(from transcript: Transcript?) -> [TranscriptKeyword] {
        guard let transcript, !transcript.isEmpty else { return [] }

        let tokens = tokenize(transcript.fullText)
        guard !tokens.isEmpty else { return [] }

        var phraseCounts: [String: Int] = [:]
        var nounCounts: [String: Int] = [:]
        var wordCounts: [String: Int] = [:]

        for index in tokens.indices {
            let current = tokens[index]
            guard current.isUsable else { continue }

            wordCounts[current.text, default: 0] += 1

            if current.isNoun, current.text.count >= 4 {
                nounCounts[current.text, default: 0] += 1
            }

            // Only pair words that were genuinely adjacent in the speech.
            guard index + 1 < tokens.count else { continue }
            let next = tokens[index + 1]
            guard next.isUsable, next.isNoun else { continue }
            guard current.isNoun || current.isAdjective else { continue }

            phraseCounts["\(current.text) \(next.text)", default: 0] += 1
        }

        // A phrase said twice is a topic. A phrase said once still counts when
        // both of its words recur on their own, which is how a real subject like
        // "halloween candles" survives being mentioned only once.
        let phrases = phraseCounts
            .filter { entry in
                if entry.value >= 2 { return true }

                let parts = entry.key.split(separator: " ").map(String.init)
                return parts.allSatisfy { (wordCounts[$0] ?? 0) >= 3 }
            }
            .map { TranscriptKeyword(phrase: $0.key, count: $0.value) }
            .sorted(by: strongestFirst)

        let coveredWords = Set(phrases.flatMap { $0.phrase.split(separator: " ").map(String.init) })

        let nouns = nounCounts
            .filter { $0.value >= 3 && !coveredWords.contains($0.key) }
            .map { TranscriptKeyword(phrase: $0.key, count: $0.value) }
            .sorted(by: strongestFirst)

        return phrases + nouns
    }

    private static func strongestFirst(
        _ lhs: TranscriptKeyword,
        _ rhs: TranscriptKeyword
    ) -> Bool {
        if lhs.count == rhs.count {
            return lhs.phrase < rhs.phrase
        }
        return lhs.count > rhs.count
    }

    /// Picks the single most descriptive phrase in a short window of speech.
    private static func bestPhrase(in tokens: [Token]) -> String? {
        var fallbackNoun: String?

        for index in tokens.indices {
            let current = tokens[index]
            guard current.isUsable else { continue }

            if current.isNoun, current.text.count >= 4, fallbackNoun == nil {
                fallbackNoun = current.text
            }

            guard index + 1 < tokens.count else { continue }
            let next = tokens[index + 1]
            guard next.isUsable, next.isNoun else { continue }
            guard current.isNoun || current.isAdjective else { continue }

            return "\(current.text) \(next.text)"
        }

        return fallbackNoun
    }

    // MARK: - Tokenizing

    private struct Token {
        let text: String
        let isNoun: Bool
        let isAdjective: Bool
        let isUsable: Bool
    }

    private static func tokenize(_ text: String) -> [Token] {
        guard !text.isEmpty else { return [] }

        var tokens: [Token] = []
        let tagger = NLTagger(tagSchemes: [.lexicalClass])
        tagger.string = text

        tagger.enumerateTags(
            in: text.startIndex..<text.endIndex,
            unit: .word,
            scheme: .lexicalClass,
            options: [.omitPunctuation, .omitWhitespace]
        ) { tag, range in
            // Apostrophes are dropped rather than split on, so "don't" stays a
            // single stop word instead of becoming the bogus token "don".
            let word = String(text[range])
                .lowercased()
                .replacingOccurrences(of: "'", with: "")
                .replacingOccurrences(of: "\u{2019}", with: "")
                .trimmingCharacters(in: CharacterSet.letters.inverted)

            let isNoun = tag == .noun
            let isAdjective = tag == .adjective

            let usable = word.count >= 3
                && !stopWords.contains(word)
                && (isNoun || isAdjective)

            tokens.append(
                Token(
                    text: word,
                    isNoun: isNoun,
                    isAdjective: isAdjective,
                    isUsable: usable
                )
            )

            return true
        }

        return tokens
    }

    // MARK: - Formatting

    private static func titleCase(_ value: String) -> String {
        value
            .split(separator: " ")
            .map { $0.prefix(1).uppercased() + $0.dropFirst() }
            .joined(separator: " ")
    }

    // MARK: - Vocabulary

    /// Conversational filler plus nouns too generic to describe anything.
    /// Contraction stems are included because dictation splits them
    /// inconsistently between "don't", "dont", and "don".
    private static let stopWords: Set<String> = [
        "about", "actually", "after", "again", "all", "almost", "already",
        "alright", "also", "always", "and", "another", "any", "anything",
        "are", "aren", "around", "away", "back", "because", "been", "before",
        "being", "best", "better", "big", "bit", "both", "bring", "but",
        "buy", "call", "came", "can", "cannot", "cant", "come", "coming",
        "could", "couldn", "couldnt", "cute", "day", "definitely", "did",
        "didn", "didnt", "does", "doesn", "doesnt", "doing", "don", "done",
        "dont", "down", "each", "either", "else", "even", "ever", "every",
        "everything", "exactly", "far", "few", "find", "first", "for", "from",
        "get", "gets", "getting", "give", "goes", "going", "gonna", "good",
        "got", "gotta", "great", "guess", "guy", "guys", "had", "hadn", "has",
        "hasn", "have", "haven", "havent", "having", "her", "here", "hers",
        "hey", "him", "his", "how", "huh", "isn", "its", "ive", "just",
        "keep", "kind", "kinda", "know", "last", "lemme", "lets", "like",
        "little", "long", "look", "looked", "looking", "looks", "lot", "love",
        "made", "make", "makes", "many", "maybe", "mean", "might", "mine",
        "more", "most", "much", "must", "need", "never", "new", "next",
        "nice", "not", "nothing", "now", "off", "oh", "okay", "old", "once",
        "one", "only", "other", "our", "out", "over", "own", "part", "people",
        "place", "pretty", "probably", "put", "quite", "real", "really",
        "right", "said", "same", "saw", "say", "says", "see", "seen", "she",
        "should", "shouldn", "show", "side", "since", "some", "someone",
        "something", "sometimes", "soon", "sort", "stuff", "such", "super",
        "sure", "take", "tell", "than", "that", "thats", "the", "their",
        "them", "then", "there", "theres", "these", "they", "thing", "things",
        "think", "this", "those", "though", "thought", "three", "through",
        "time", "today", "together", "too", "took", "top", "try", "trying",
        "turn", "two", "under", "until", "use", "very", "wait", "wanna",
        "want", "was", "wasn", "wasnt", "watch", "way", "well", "went",
        "were", "weren", "what", "whats", "when", "where", "which", "while",
        "who", "why", "will", "with", "without", "won", "wont", "would",
        "wouldn", "wow", "yeah", "yep", "yes", "yet", "you", "your", "youre"
    ]
}
