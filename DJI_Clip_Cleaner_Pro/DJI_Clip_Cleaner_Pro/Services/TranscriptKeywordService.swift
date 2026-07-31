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

    /// Subjects covered in the video, formatted for a written description.
    /// Store names are kept out of this list — they have their own section.
    static func topics(from transcript: Transcript?, limit: Int = 8) -> [String] {
        let storeNames = knownStoreDisplayNames

        return ranked(from: transcript)
            .filter { keyword in
                !storeNames.contains(keyword.phrase.lowercased())
                    && !keyword.phrase.split(separator: " ").contains(where: {
                        storeNames.contains($0.lowercased())
                    })
                    && !isWeakTopic(keyword.phrase)
            }
            // Prefer real finds ("halloween candles") over bare nouns ("sugar").
            // Story/travel phrases outrank generic bigrams when both appear.
            .sorted { lhs, rhs in
                let leftStory = storySignalScore(lhs.phrase)
                let rightStory = storySignalScore(rhs.phrase)
                if leftStory != rightStory {
                    return leftStory > rightStory
                }
                let leftPhrase = lhs.phrase.contains(" ")
                let rightPhrase = rhs.phrase.contains(" ")
                if leftPhrase != rightPhrase {
                    return leftPhrase && !rightPhrase
                }
                return strongestFirst(lhs, rhs)
            }
            .prefix(limit)
            .map { titleCase($0.phrase) }
    }

    /// Stores named in the video. Only the curated retailer list is trusted —
    /// Apple's name tagger happily labels cities and misheard speech as stores
    /// ("San Marcos", "medicine Bumgardner"), which must never reach YouTube.
    static func places(from transcript: Transcript?, limit: Int = 6) -> [String] {
        guard let transcript, !transcript.isEmpty else { return [] }

        let haystack = " " + transcript.fullText
            .lowercased()
            .components(separatedBy: CharacterSet.alphanumerics.inverted)
            .joined(separator: " ")
            .replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression) + " "

        var found: [String] = []

        for (needle, display) in knownPlaces {
            guard haystack.contains(" \(needle) ") else { continue }
            guard !found.contains(display) else { continue }
            found.append(display)
        }

        return Array(found.prefix(limit))
    }

    /// A readable title for one stretch of speech, or nil when that stretch has
    /// nothing worth naming. Callers should skip the chapter rather than fall
    /// back to raw transcript text. Single nouns like "Sugar" are rejected —
    /// a chapter needs a two-word subject.
    static func chapterTitle(from text: String) -> String? {
        guard let phrase = bestPhrase(in: tokenize(text), requireTwoWords: true) else {
            return nil
        }

        let title = titleCase(phrase)
        guard title.count <= maximumTitleLength else { return nil }
        guard title.split(separator: " ").count >= 2 else { return nil }

        return title
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

        return spread(phrases + nouns)
    }

    /// Keeps one subject from swamping the list. Without this a Halloween video
    /// returns "pumpkin spice", "halloween pumpkin", "bat pumpkin" and
    /// "spice spice" as four separate topics.
    private static func spread(_ keywords: [TranscriptKeyword]) -> [TranscriptKeyword] {
        var timesUsed: [String: Int] = [:]
        var kept: [TranscriptKeyword] = []

        for keyword in keywords {
            let words = keyword.phrase.split(separator: " ").map(String.init)

            // "spice spice" / "flight flights" are stutters or ASR doubles, not subjects.
            if words.count == 2 {
                if words[0] == words[1] { continue }
                if wordStem(words[0]) == wordStem(words[1]) { continue }
            }

            // One appearance of "pumpkin" across the whole list is enough.
            // Same stem ("flight"/"flights") also blocks a second near-duplicate.
            guard words.allSatisfy({ word in
                (timesUsed[word] ?? 0) < 1 && (timesUsed[wordStem(word)] ?? 0) < 1
            }) else { continue }

            for word in words {
                timesUsed[word, default: 0] += 1
                timesUsed[wordStem(word), default: 0] += 1
            }
            kept.append(keyword)
        }

        return kept
    }

    /// Rough singular/plural stem so "flight flights" collapses.
    private static func wordStem(_ word: String) -> String {
        if word.count <= 3 { return word }
        if word.hasSuffix("ies"), word.count > 4 {
            return String(word.dropLast(3)) + "y"
        }
        if word.hasSuffix("sses") || word.hasSuffix("xes") || word.hasSuffix("zes") {
            return String(word.dropLast(2))
        }
        if word.hasSuffix("s"), !word.hasSuffix("ss") {
            return String(word.dropLast())
        }
        return word
    }

    private static func isWeakTopic(_ phrase: String) -> Bool {
        let words = phrase.lowercased().split(separator: " ").map(String.init)
        if words.isEmpty { return true }
        // Lone ultra-generic nouns never belong in WHAT WE FOUND / chapters.
        if words.count == 1 {
            return weakTopicWords.contains(words[0])
        }
        // Both sides weak → junk ("downstairs area", "entire schedule").
        return words.allSatisfy { weakTopicWords.contains($0) }
    }

    private static func storySignalScore(_ phrase: String) -> Int {
        phrase
            .lowercased()
            .split(separator: " ")
            .map { storyBoostWords[String($0)] ?? 0 }
            .reduce(0, +)
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

    /// Picks the most descriptive phrase in a short window of speech.
    /// When `requireTwoWords` is true (chapters), a lone noun is never enough.
    private static func bestPhrase(
        in tokens: [Token],
        requireTwoWords: Bool = false
    ) -> String? {
        var fallbackNoun: String?
        var bestTwoWord: String?
        var bestScore = Int.min

        for index in tokens.indices {
            let current = tokens[index]
            guard current.isUsable else { continue }

            if current.isNoun, current.text.count >= 4, fallbackNoun == nil,
               !weakTopicWords.contains(current.text) {
                fallbackNoun = current.text
            }

            guard index + 1 < tokens.count else { continue }
            let next = tokens[index + 1]
            guard next.isUsable, next.isNoun else { continue }
            guard current.isNoun || current.isAdjective else { continue }

            // Skip ASR doubles ("flight flights") and weak pairings.
            if wordStem(current.text) == wordStem(next.text) { continue }
            let phrase = "\(current.text) \(next.text)"
            if isWeakTopic(phrase) { continue }

            var score = current.text.count + next.text.count
            score += storySignalScore(phrase) * 8

            if knownStoreDisplayNames.contains(current.text)
                || knownStoreDisplayNames.contains(next.text) {
                score += 12
            }

            // Role + misheard first name ("coworker Brian") is weak chapter bait.
            if personRoleWords.contains(current.text) {
                score -= 10
            }

            if score > bestScore {
                bestScore = score
                bestTwoWord = phrase
            }
        }

        if let bestTwoWord {
            return bestTwoWord
        }

        return requireTwoWords ? nil : fallbackNoun
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

    /// Speech-to-text mangles brand names constantly, so each store is matched
    /// on the spellings dictation actually produces. Keys must be lowercase and
    /// space-separated to match the normalized transcript.
    ///
    /// Only this list is ever treated as a store. Guessing from the name tagger
    /// is deliberately not used — that path invented "San Marcos" (a city) and
    /// "medicine Bumgardner" (misheard speech) as stores.
    private static let knownPlaces: [(String, String)] = [
        ("homegoods", "HomeGoods"),
        ("home goods", "HomeGoods"),
        ("homesense", "HomeSense"),
        ("home sense", "HomeSense"),
        ("tj maxx", "T.J. Maxx"),
        ("tjmaxx", "T.J. Maxx"),
        ("t j maxx", "T.J. Maxx"),
        ("marshalls", "Marshalls"),
        ("ross", "Ross"),
        ("target", "Target"),
        ("walmart", "Walmart"),
        ("michaels", "Michaels"),
        ("hobby lobby", "Hobby Lobby"),
        ("at home", "At Home"),
        ("big lots", "Big Lots"),
        ("spirit halloween", "Spirit Halloween"),
        ("dollar tree", "Dollar Tree"),
        ("dollar general", "Dollar General"),
        ("five below", "Five Below"),
        ("kirklands", "Kirkland's"),
        ("world market", "World Market"),
        ("ikea", "IKEA"),
        ("costco", "Costco"),
        ("sams club", "Sam's Club"),
        ("lowes", "Lowe's"),
        ("home depot", "The Home Depot"),
        ("party city", "Party City"),
        ("burlington", "Burlington"),
        ("trader joes", "Trader Joe's"),
        ("whole foods", "Whole Foods"),
        ("aldi", "Aldi"),
        ("heb", "H-E-B"),
        ("h e b", "H-E-B"),
        ("kroger", "Kroger"),
        ("bath and body works", "Bath & Body Works"),
        ("barnes and noble", "Barnes & Noble"),
        ("hallmark", "Hallmark"),
        ("joann", "JOANN"),
        ("ace hardware", "Ace Hardware"),
        ("buc ees", "Buc-ee's"),
        ("bucees", "Buc-ee's"),
        ("cracker barrel", "Cracker Barrel"),
        ("ikes love and sandwiches", "Ike's Love and Sandwiches"),
        ("ikes love", "Ike's Love and Sandwiches"),
        ("ikes sandwiches", "Ike's Love and Sandwiches"),
        ("ikes sandwich", "Ike's Love and Sandwiches"),
        ("ike s love", "Ike's Love and Sandwiches"),
        ("ike love", "Ike's Love and Sandwiches"),
        // Travel / airports — needed for delay/trip vlogs, not retail hunts.
        ("dfw", "DFW"),
        ("dallas fort worth", "DFW"),
        ("dallas/fort worth", "DFW"),
        ("american airlines", "American Airlines"),
        ("american airline", "American Airlines"),
        ("southwest airlines", "Southwest Airlines"),
        ("delta airlines", "Delta"),
        ("united airlines", "United"),
        ("omaha", "Omaha"),
        ("austin", "Austin"),
        ("austin bergstrom", "Austin"),
        ("bag claim", "Baggage Claim")
    ]

    private static var knownStoreDisplayNames: Set<String> {
        var names = Set(knownPlaces.map { $0.1.lowercased() })
        // Single-token aliases so "ross" in a topic phrase is recognized as a store.
        names.formUnion([
            "homegoods", "homesense", "ross", "target", "walmart", "marshalls",
            "michaels", "costco", "burlington", "aldi", "heb", "kroger", "ikea"
        ])
        return names
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

    /// Words that look like topics but never describe the story by themselves.
    private static let weakTopicWords: Set<String> = [
        "area", "brand", "downstairs", "entire", "ground", "internet",
        "nationwide", "schedule", "short", "speed", "ups", "update",
        "video", "walkthrough", "upstairs", "section", "moment", "minutes"
    ]

    private static let personRoleWords: Set<String> = [
        "coworker", "colleague", "friend", "boss", "manager", "husband",
        "wife", "boyfriend", "girlfriend"
    ]

    /// Travel / conflict lexicon — boost these for topics and chapter titles.
    private static let storyBoostWords: [String: Int] = [
        "delay": 5, "delayed": 5, "delays": 5,
        "missed": 5, "miss": 4,
        "cancelled": 5, "canceled": 5, "cancellation": 4,
        "flight": 3, "flights": 3, "airline": 3, "airlines": 3,
        "airport": 4, "terminal": 3, "gate": 3,
        "boarding": 3, "baggage": 2, "luggage": 2,
        "trip": 3, "business": 3, "ground": 2, "stop": 2,
        "dfw": 5, "omaha": 3, "austin": 2,
        "hours": 3, "late": 3, "stuck": 4
    ]
}
