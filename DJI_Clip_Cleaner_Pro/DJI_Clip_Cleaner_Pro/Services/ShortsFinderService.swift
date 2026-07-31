import AVFoundation
import Foundation

/// One cut inside a spliced Short — hook, payoff, or button.
struct ShortBeat: Identifiable, Sendable {
    enum Role: String, Sendable {
        case hook
        case payoff
        case button

        var label: String {
            switch self {
            case .hook: return "HOOK"
            case .payoff: return "PAYOFF"
            case .button: return "BUTTON"
            }
        }
    }

    let id: UUID
    let role: Role
    let startTime: TimeInterval
    let duration: TimeInterval
    let quote: String

    var endTime: TimeInterval { startTime + duration }

    var formattedRange: String {
        "\(ShortCandidate.timecode(startTime))–\(ShortCandidate.timecode(endTime))"
    }
}

/// A Short assembled by splicing 2–3 beats from different places in the long video.
struct ShortCandidate: Identifiable, Sendable {
    let id: UUID
    let beats: [ShortBeat]
    let score: Double
    let speechCoverage: Double
    let motionLevel: Double
    let startsOnSpeech: Bool
    let projectedHook: Int
    let projectedRetention: Int
    let bestTitle: String
    let storySummary: String

    var startTime: TimeInterval { beats.first?.startTime ?? 0 }

    var duration: TimeInterval {
        beats.reduce(0) { $0 + $1.duration }
    }

    var endTime: TimeInterval { startTime + duration }

    var quote: String {
        beats
            .map { $0.quote.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
            .joined(separator: " / ")
    }

    var hookLine: String {
        let payoff = beats.first(where: { $0.role == .payoff })?.quote
            ?? beats.first?.quote
            ?? bestTitle
        let cleaned = payoff.trimmingCharacters(in: .whitespacesAndNewlines)
        let words = cleaned.split(separator: " ").prefix(8).joined(separator: " ")
        return words.isEmpty ? bestTitle : words
    }

    var formattedRange: String {
        beats.map { "\($0.role.label) \($0.formattedRange)" }.joined(separator: " · ")
    }

    var formattedDuration: String {
        "\(Int(duration.rounded())) sec · \(beats.count) cuts"
    }

    var scorePercent: Int {
        Int((score * 100).rounded())
    }

    var reason: String {
        if beats.count >= 2 {
            return "Spliced \(beats.map(\.role.label).joined(separator: " → ")) into one story"
        }
        return "Single continuous moment"
    }

    static func timecode(_ seconds: TimeInterval) -> String {
        let total = Int(seconds.rounded())
        return String(format: "%d:%02d", total / 60, total % 60)
    }
}

enum ShortsFinderService {
    enum TargetLength: Double, CaseIterable, Identifiable, Sendable {
        case punchy = 20
        case standard = 30
        case extended = 45
        case fullMinute = 60
        case story = 90

        var id: Double { rawValue }

        var displayName: String {
            switch self {
            case .punchy: return "20s"
            case .standard: return "30s"
            case .extended: return "45s"
            case .fullMinute: return "60s"
            case .story: return "90s"
            }
        }

        var guidance: String {
            switch self {
            case .punchy:
                return "Tight story: hook + payoff + quick button."
            case .standard:
                return "Best default. Three cuts spliced into one Short."
            case .extended:
                return "More room on the payoff find."
            case .fullMinute:
                return "Longer payoff — only if the find needs time."
            case .story:
                return "Extended assembly. Needs a strong transcript."
            }
        }
    }

    private static let windowSeconds = 0.5
    private static let speechThreshold: Float = 0.012

    static func findCandidates(
        in videoURL: URL,
        targetLength: TargetLength,
        transcript: Transcript? = nil,
        brand: BrandSettingsValues,
        preset: BrandPreset,
        longFormTitle: String,
        maximumResults: Int = 5
    ) async -> [ShortCandidate] {
        let asset = AVURLAsset(url: videoURL)

        guard let durationValue = try? await asset.load(.duration) else {
            return []
        }

        let duration = CMTimeGetSeconds(durationValue)
        let target = targetLength.rawValue

        guard duration.isFinite, duration > 12 else {
            return []
        }

        // Story mode needs speech. Without a transcript we only have energy —
        // fall back to continuous windows so the tab still does something.
        if let transcript, !transcript.isEmpty {
            return assembleStories(
                transcript: transcript,
                videoDuration: duration,
                target: target,
                brand: brand,
                preset: preset,
                longFormTitle: longFormTitle,
                maximumResults: maximumResults
            )
        }

        return await continuousFallbacks(
            asset: asset,
            duration: duration,
            target: target,
            brand: brand,
            preset: preset,
            longFormTitle: longFormTitle,
            maximumResults: maximumResults
        )
    }

    // MARK: - Story assembly (transcript required)

    private struct Phrase {
        let start: TimeInterval
        let end: TimeInterval
        let text: String

        var duration: TimeInterval { max(end - start, 0.4) }
        var mid: TimeInterval { (start + end) / 2 }
    }

    private static func assembleStories(
        transcript: Transcript,
        videoDuration: TimeInterval,
        target: TimeInterval,
        brand: BrandSettingsValues,
        preset: BrandPreset,
        longFormTitle: String,
        maximumResults: Int
    ) -> [ShortCandidate] {
        let phrases = buildPhrases(from: transcript)
        guard phrases.count >= 2 else { return [] }

        let scored = phrases.map { phrase -> (Phrase, Double, Double, Double) in
            (
                phrase,
                hookScore(phrase.text, preset: preset),
                findScore(phrase.text, preset: preset),
                reactionScore(phrase.text, preset: preset)
            )
        }

        let payoffs = scored
            .filter { $0.2 >= 0.15 || $0.1 + $0.2 + $0.3 >= 0.35 }
            .sorted { lhs, rhs in
                (lhs.2 * 1.4 + lhs.1 * 0.4 + lhs.3 * 0.3) >
                    (rhs.2 * 1.4 + rhs.1 * 0.4 + rhs.3 * 0.3)
            }

        var stories: [ShortCandidate] = []
        var usedPayoffMids: [TimeInterval] = []

        for (payoff, hookS, findS, reactS) in payoffs {
            if usedPayoffMids.contains(where: { abs($0 - payoff.mid) < 25 }) {
                continue
            }

            let hook = scored
                .filter { $0.0.end <= payoff.start - 0.5 }
                .filter { payoff.start - $0.0.end < 180 }
                .max(by: { $0.1 < $1.1 })
                ?? scored
                    .filter { $0.0.end <= payoff.start - 0.5 }
                    .max(by: { $0.1 + $0.2 < $1.1 + $1.2 })

            let button = scored
                .filter { $0.0.start >= payoff.end + 0.3 }
                .filter { $0.0.start - payoff.end < 120 }
                .max(by: { $0.3 < $1.3 })
                ?? scored
                    .filter { $0.0.start >= payoff.end + 0.3 }
                    .max(by: { $0.2 + $0.3 < $1.2 + $1.3 })

            guard let hook else { continue }

            let budget = beatBudget(target: target)
            var beats: [ShortBeat] = [
                makeBeat(
                    role: .hook,
                    phrase: hook.0,
                    desired: budget.hook,
                    videoDuration: videoDuration
                ),
                makeBeat(
                    role: .payoff,
                    phrase: payoff,
                    desired: budget.payoff,
                    videoDuration: videoDuration
                )
            ]

            if let button, button.0.start > payoff.end {
                beats.append(
                    makeBeat(
                        role: .button,
                        phrase: button.0,
                        desired: budget.button,
                        videoDuration: videoDuration
                    )
                )
            }

            let titleSeed = cleanTitleSeed(from: payoff.text, preset: preset, fallback: longFormTitle)
            let title = ShortsMetadataService.bestTitle(
                quote: titleSeed,
                longFormTitle: longFormTitle,
                brand: brand,
                preset: preset
            )

            let total = beats.reduce(0.0) { $0 + $1.duration }
            let overall = min((findS * 0.5) + (hookS * 0.25) + (reactS * 0.15) + 0.2, 1.0)
            let summary = storySummary(beats: beats, preset: preset)

            stories.append(
                ShortCandidate(
                    id: UUID(),
                    beats: beats,
                    score: overall,
                    speechCoverage: 0.85,
                    motionLevel: 0.45,
                    startsOnSpeech: true,
                    projectedHook: min(max(Int(70 + overall * 25), 1), 99),
                    projectedRetention: min(max(Int(68 + overall * 22 - (total > 40 ? 4 : 0)), 1), 99),
                    bestTitle: title,
                    storySummary: summary
                )
            )

            usedPayoffMids.append(payoff.mid)
            if stories.count >= maximumResults {
                break
            }
        }

        return stories.sorted { $0.score > $1.score }
    }

    private static func beatBudget(target: TimeInterval) -> (hook: TimeInterval, payoff: TimeInterval, button: TimeInterval) {
        let hook = min(max(target * 0.22, 3.0), 6.0)
        let button = min(max(target * 0.18, 3.0), 5.5)
        let payoff = max(target - hook - button, target * 0.45)
        return (hook, payoff, button)
    }

    private static func makeBeat(
        role: ShortBeat.Role,
        phrase: Phrase,
        desired: TimeInterval,
        videoDuration: TimeInterval
    ) -> ShortBeat {
        // Center the cut on the spoken phrase, pad slightly for picture.
        let pad = min(0.35, desired * 0.08)
        var start = max(phrase.start - pad, 0)
        var end = min(max(phrase.end + pad, start + 1.2), videoDuration)
        var duration = end - start

        if duration > desired {
            let overflow = duration - desired
            start += overflow * 0.35
            end = start + desired
            duration = desired
        } else if duration < desired * 0.75 {
            let need = desired - duration
            start = max(start - need * 0.3, 0)
            end = min(start + desired, videoDuration)
            duration = end - start
        }

        return ShortBeat(
            id: UUID(),
            role: role,
            startTime: start,
            duration: duration,
            quote: phrase.text
        )
    }

    private static func buildPhrases(from transcript: Transcript) -> [Phrase] {
        let segments = transcript.segments.sorted { $0.startTime < $1.startTime }
        guard !segments.isEmpty else { return [] }

        var phrases: [Phrase] = []
        var bucket: [TranscriptSegment] = []

        func flush() {
            guard !bucket.isEmpty else { return }
            let text = bucket.map(\.text).joined(separator: " ")
                .trimmingCharacters(in: .whitespacesAndNewlines)
            let start = bucket.first!.startTime
            let end = bucket.last!.endTime
            if !text.isEmpty, end > start {
                phrases.append(Phrase(start: start, end: end, text: text))
            }
            bucket = []
        }

        for segment in segments {
            if let last = bucket.last, segment.startTime - last.endTime > 0.85 {
                flush()
            }

            bucket.append(segment)

            let span = (bucket.last!.endTime) - (bucket.first!.startTime)
            let words = bucket.map(\.text).joined(separator: " ").split(separator: " ").count
            if span >= 6.5 || words >= 14 {
                flush()
            }
        }

        flush()
        return phrases.filter { $0.duration >= 1.2 && $0.duration <= 14 }
    }

    private static func hookScore(_ text: String, preset: BrandPreset) -> Double {
        let lower = text.lowercased()
        let keys = [
            "look at", "look at this", "check this", "check out", "wait until",
            "wait till", "oh my", "oh wow", "holy", "yo ", "here we go",
            "coming up", "next place", "headed to", "walk in"
        ] + presetHookExtras(preset)
        return keywordScore(lower, keys: keys)
    }

    private static func findScore(_ text: String, preset: BrandPreset) -> Double {
        let lower = text.lowercased()
        let keys = [
            "candle", "halloween", "pumpkin", "skeleton", "spider", "witch",
            "decor", "aisle", "shelf", "found", "this one", "these are",
            "sandwich", "price", "dollars", "bucks", "display", "sign"
        ] + presetFindExtras(preset)

        var score = keywordScore(lower, keys: keys)
        // Prefer phrases that name a concrete thing (has a longer content word).
        let meaty = lower.split(separator: " ").filter { $0.count >= 5 }.count
        score += min(Double(meaty) * 0.04, 0.2)
        return min(score, 1.0)
    }

    private static func reactionScore(_ text: String, preset: BrandPreset) -> Double {
        let lower = text.lowercased()
        let keys = [
            "gonna buy", "going to buy", "love this", "really good", "so good",
            "creepy", "scary", "cute", "perfect", "need this", "taking this",
            "that's crazy", "no way", "come on"
        ] + presetReactionExtras(preset)
        return keywordScore(lower, keys: keys)
    }

    private static func keywordScore(_ lower: String, keys: [String]) -> Double {
        var score = 0.0
        for key in keys where lower.contains(key) {
            score += 0.18
        }
        return min(score, 1.0)
    }

    private static func presetHookExtras(_ preset: BrandPreset) -> [String] {
        preset.hookExtras
    }

    private static func presetFindExtras(_ preset: BrandPreset) -> [String] {
        preset.findExtras
    }

    private static func presetReactionExtras(_ preset: BrandPreset) -> [String] {
        preset.reactionExtras
    }

    private static func cleanTitleSeed(
        from text: String,
        preset: BrandPreset,
        fallback: String
    ) -> String {
        var words = text
            .split(separator: " ")
            .map(String.init)
            .filter { word in
                let lower = word.lowercased()
                if lower.allSatisfy(\.isNumber) { return false }
                if ["we're", "gonna", "going", "just", "like", "this", "that", "have", "here"].contains(lower) {
                    return false
                }
                return word.count > 1
            }

        // Keep the interesting middle of the phrase.
        if words.count > 8 {
            words = Array(words.prefix(8))
        }

        let joined = words.joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
        if joined.split(separator: " ").count >= 3 {
            return joined
        }

        if !fallback.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return fallback
        }

        return preset.fallbackShortTitle
    }

    private static func storySummary(beats: [ShortBeat], preset: BrandPreset) -> String {
        let roles = beats.map(\.role.label).joined(separator: " → ")
        switch preset {
        case .halloweenHunt:
            return "Halloween story cut: \(roles). Opens on curiosity, lands on the find, ends before the full hunt is spoiled."
        case .storeWalk, .shoppingHaul:
            return "Store-walk story cut: \(roles). Walk-up, the item, then the reaction."
        case .travelDay, .workTravel:
            return "Travel story cut: \(roles). Plan, obstacle, payoff tease."
        case .themeParkDay:
            return "Park-day story cut: \(roles). Arrive, highlight, reaction."
        case .foodRestaurants:
            return "Food story cut: \(roles). Order, bite, verdict tease."
        default:
            return "Story cut: \(roles). Separate moments spliced into one Short."
        }
    }

    // MARK: - Continuous fallback (no transcript)

    private static func continuousFallbacks(
        asset: AVURLAsset,
        duration: TimeInterval,
        target: TimeInterval,
        brand: BrandSettingsValues,
        preset: BrandPreset,
        longFormTitle: String,
        maximumResults: Int
    ) async -> [ShortCandidate] {
        guard duration > target + 1 else { return [] }

        let energies = await audioEnergyTimeline(asset: asset)
        guard !energies.isEmpty else { return [] }

        let windowsPerCandidate = max(Int(target / windowSeconds), 1)
        let step = max(Int(2.0 / windowSeconds), 1)
        var scored: [(start: TimeInterval, score: Double, coverage: Double)] = []
        var index = 0

        while index + windowsPerCandidate <= energies.count {
            let slice = energies[index..<(index + windowsPerCandidate)]
            let startTime = Double(index) * windowSeconds
            let active = slice.filter { $0 >= speechThreshold }.count
            let coverage = Double(active) / Double(slice.count)
            let mean = slice.reduce(0, +) / Float(slice.count)
            let score = (coverage * 0.7) + (Double(min(mean, 1)) * 0.3)

            if coverage >= 0.35 {
                scored.append((startTime, score, coverage))
            }
            index += step
        }

        scored.sort { $0.score > $1.score }

        var picks: [ShortCandidate] = []
        var used: [TimeInterval] = []

        for item in scored {
            if used.contains(where: { abs($0 - item.start) < target * 0.8 }) {
                continue
            }

            let title = ShortsMetadataService.bestTitle(
                quote: "",
                longFormTitle: longFormTitle,
                brand: brand,
                preset: preset
            )

            let beat = ShortBeat(
                id: UUID(),
                role: .payoff,
                startTime: item.start,
                duration: target,
                quote: ""
            )

            picks.append(
                ShortCandidate(
                    id: UUID(),
                    beats: [beat],
                    score: item.score,
                    speechCoverage: item.coverage,
                    motionLevel: 0.3,
                    startsOnSpeech: true,
                    projectedHook: Int(60 + item.score * 25),
                    projectedRetention: Int(58 + item.coverage * 25),
                    bestTitle: title,
                    storySummary: "Continuous fallback cut — transcribe the video to unlock real story splicing."
                )
            )
            used.append(item.start)
            if picks.count >= maximumResults { break }
        }

        return picks
    }

    private static func audioEnergyTimeline(asset: AVURLAsset) async -> [Float] {
        guard let track = try? await asset.loadTracks(withMediaType: .audio).first else {
            return []
        }

        let reader: AVAssetReader
        do {
            reader = try AVAssetReader(asset: asset)
        } catch {
            return []
        }

        let output = AVAssetReaderTrackOutput(
            track: track,
            outputSettings: [
                AVFormatIDKey: kAudioFormatLinearPCM,
                AVLinearPCMBitDepthKey: 16,
                AVLinearPCMIsBigEndianKey: false,
                AVLinearPCMIsFloatKey: false,
                AVLinearPCMIsNonInterleaved: false,
                AVSampleRateKey: 16_000,
                AVNumberOfChannelsKey: 1
            ]
        )
        output.alwaysCopiesSampleData = false
        reader.add(output)

        guard reader.startReading() else { return [] }

        var energies: [Float] = []
        let bytesPerWindow = Int(16_000 * windowSeconds) * 2
        var leftover = Data()

        while reader.status == .reading {
            guard let sample = output.copyNextSampleBuffer(),
                  let block = CMSampleBufferGetDataBuffer(sample) else {
                break
            }

            let length = CMBlockBufferGetDataLength(block)
            var data = Data(count: length)
            data.withUnsafeMutableBytes { raw in
                guard let base = raw.baseAddress else { return }
                CMBlockBufferCopyDataBytes(block, atOffset: 0, dataLength: length, destination: base)
            }

            leftover.append(data)

            while leftover.count >= bytesPerWindow {
                let window = leftover.prefix(bytesPerWindow)
                leftover.removeFirst(bytesPerWindow)
                energies.append(rootMeanSquare(window))
            }
        }

        return energies
    }

    private static func rootMeanSquare(_ data: Data) -> Float {
        guard data.count >= 2 else { return 0 }

        var sum: Float = 0
        var count = 0
        data.withUnsafeBytes { raw in
            let samples = raw.bindMemory(to: Int16.self)
            for sample in samples {
                let value = Float(sample) / Float(Int16.max)
                sum += value * value
                count += 1
            }
        }

        guard count > 0 else { return 0 }
        return sqrt(sum / Float(count))
    }
}
