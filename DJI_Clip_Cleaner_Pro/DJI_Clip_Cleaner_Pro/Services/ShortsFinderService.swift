import AVFoundation
import Foundation

struct ShortCandidate: Identifiable, Sendable {
    let id: UUID
    let startTime: TimeInterval
    let duration: TimeInterval
    let score: Double
    let speechCoverage: Double
    let motionLevel: Double
    let startsOnSpeech: Bool
    let quote: String

    var endTime: TimeInterval {
        startTime + duration
    }

    var formattedRange: String {
        "\(ShortCandidate.timecode(startTime)) – \(ShortCandidate.timecode(endTime))"
    }

    var scorePercent: Int {
        Int((score * 100).rounded())
    }

    /// Plain-language explanation of why this moment was picked.
    var reason: String {
        var parts: [String] = []

        if !quote.isEmpty {
            parts.append("clear spoken line")
        }

        if speechCoverage >= 0.75 {
            parts.append("talking throughout")
        } else if speechCoverage >= 0.5 {
            parts.append("mostly talking")
        }

        if motionLevel >= 0.6 {
            parts.append("lots of movement")
        } else if motionLevel >= 0.3 {
            parts.append("some movement")
        }

        if startsOnSpeech {
            parts.append("starts on a clean line")
        }

        return parts.isEmpty ? "Steady moment" : parts.joined(separator: ", ")
    }

    static func timecode(_ seconds: TimeInterval) -> String {
        let total = Int(seconds.rounded())
        return String(format: "%d:%02d", total / 60, total % 60)
    }
}

enum ShortsFinderService {
    /// YouTube pushes Shorts wider at roughly 65% retention under 30 seconds and
    /// 50% between 30 and 60, so the presets stay inside the easier bands.
    enum TargetLength: Double, CaseIterable, Identifiable, Sendable {
        case punchy = 20
        case standard = 30
        case extended = 45

        var id: Double { rawValue }

        var displayName: String {
            switch self {
            case .punchy:
                return "20 sec"
            case .standard:
                return "30 sec"
            case .extended:
                return "45 sec"
            }
        }

        var guidance: String {
            switch self {
            case .punchy:
                return "Shortest and easiest to hold attention all the way through."
            case .standard:
                return "Good default. Enough room for a hook and a payoff."
            case .extended:
                return "More story, but needs to stay interesting for longer."
            }
        }
    }

    private static let windowSeconds = 0.5
    private static let speechThreshold: Float = 0.012
    private static let candidateStepSeconds = 1.0
    private static let minimumSpeechCoverage = 0.35
    private static let minimumGapSeconds = 2.0

    static func findCandidates(
        in videoURL: URL,
        targetLength: TargetLength,
        transcript: Transcript? = nil,
        maximumResults: Int = 5
    ) async -> [ShortCandidate] {
        let asset = AVURLAsset(url: videoURL)

        guard let durationValue = try? await asset.load(.duration) else {
            return []
        }

        let duration = CMTimeGetSeconds(durationValue)
        let target = targetLength.rawValue

        guard duration.isFinite, duration > target + 1 else {
            return []
        }

        let energies = await audioEnergyTimeline(asset: asset)
        guard !energies.isEmpty else {
            return []
        }

        let motion = await motionTimeline(asset: asset, duration: duration)

        return scoreCandidates(
            energies: energies,
            motion: motion,
            target: target,
            transcript: transcript,
            maximumResults: maximumResults
        )
    }

    // MARK: - Signals

    private static func audioEnergyTimeline(asset: AVURLAsset) async -> [Float] {
        guard let audioTrack = try? await asset.loadTracks(withMediaType: .audio).first,
              let reader = try? AVAssetReader(asset: asset) else {
            return []
        }

        let outputSettings: [String: Any] = [
            AVFormatIDKey: kAudioFormatLinearPCM,
            AVLinearPCMIsBigEndianKey: false,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMBitDepthKey: 16,
            AVNumberOfChannelsKey: 1,
            AVSampleRateKey: 16_000
        ]

        let output = AVAssetReaderTrackOutput(
            track: audioTrack,
            outputSettings: outputSettings
        )
        output.alwaysCopiesSampleData = false

        guard reader.canAdd(output) else { return [] }
        reader.add(output)
        guard reader.startReading() else { return [] }

        var energies: [Float] = []
        var sampleBuffer = Data()
        let bytesPerWindow = Int(16_000 * windowSeconds) * 2

        while reader.status == .reading {
            guard let sample = output.copyNextSampleBuffer(),
                  let block = CMSampleBufferGetDataBuffer(sample) else {
                continue
            }

            let length = CMBlockBufferGetDataLength(block)
            var chunk = Data(count: length)
            chunk.withUnsafeMutableBytes { pointer in
                guard let base = pointer.baseAddress else { return }
                CMBlockBufferCopyDataBytes(
                    block,
                    atOffset: 0,
                    dataLength: length,
                    destination: base
                )
            }

            sampleBuffer.append(chunk)

            while sampleBuffer.count >= bytesPerWindow {
                let window = sampleBuffer.prefix(bytesPerWindow)
                sampleBuffer.removeFirst(bytesPerWindow)
                energies.append(rootMeanSquare(window))
            }
        }

        return energies
    }

    /// Sampled at an adaptive interval so a long export does not turn into
    /// thousands of frame decodes.
    private static func motionTimeline(
        asset: AVURLAsset,
        duration: TimeInterval
    ) async -> [(time: TimeInterval, level: Double)] {
        let interval = max(1.0, duration / 240.0)

        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.maximumSize = CGSize(width: 240, height: 135)
        generator.requestedTimeToleranceBefore = CMTime(seconds: 0.3, preferredTimescale: 600)
        generator.requestedTimeToleranceAfter = CMTime(seconds: 0.3, preferredTimescale: 600)

        var samples: [(time: TimeInterval, level: Double)] = []
        var previous: [Int]?
        var seconds = 0.0

        while seconds < duration - 0.5 {
            let time = CMTime(seconds: seconds, preferredTimescale: 600)

            guard let image = try? generator.copyCGImage(at: time, actualTime: nil) else {
                seconds += interval
                continue
            }

            let histogram = luminanceHistogram(image)

            if let previous {
                samples.append((seconds, histogramDifference(previous, histogram)))
            }

            previous = histogram
            seconds += interval
        }

        return samples
    }

    // MARK: - Scoring

    private static func scoreCandidates(
        energies: [Float],
        motion: [(time: TimeInterval, level: Double)],
        target: TimeInterval,
        transcript: Transcript?,
        maximumResults: Int
    ) -> [ShortCandidate] {
        let peakEnergy = max(energies.max() ?? 0, 0.0001)
        let peakMotion = max(motion.map(\.level).max() ?? 0, 0.0001)

        let windowsPerCandidate = max(Int(target / windowSeconds), 1)
        let step = max(Int(candidateStepSeconds / windowSeconds), 1)

        guard energies.count >= windowsPerCandidate else {
            return []
        }

        var scored: [ShortCandidate] = []
        var index = 0

        while index + windowsPerCandidate <= energies.count {
            let slice = energies[index..<(index + windowsPerCandidate)]
            let startTime = Double(index) * windowSeconds

            let activeCount = slice.filter { $0 >= speechThreshold }.count
            let coverage = Double(activeCount) / Double(slice.count)

            if coverage < minimumSpeechCoverage {
                index += step
                continue
            }

            let meanEnergy = Double(slice.reduce(0, +)) / Double(slice.count) / Double(peakEnergy)
            let localPeak = Double(slice.max() ?? 0) / Double(peakEnergy)

            let endTime = startTime + target
            let motionInRange = motion.filter { $0.time >= startTime && $0.time <= endTime }
            let motionLevel = motionInRange.isEmpty
                ? 0
                : (motionInRange.map(\.level).reduce(0, +) / Double(motionInRange.count)) / peakMotion

            // A Short that opens mid-sentence loses people immediately, so
            // reward starts where silence turns into speech.
            let previousIsQuiet = index == 0 || energies[index - 1] < speechThreshold
            let startsOnSpeech = previousIsQuiet && (slice.first ?? 0) >= speechThreshold

            let quote = transcript?
                .text(overlapping: startTime, duration: target) ?? ""
            let wordCount = quote.split(separator: " ").count
            let transcriptBoost = transcriptBoost(for: quote)

            var score =
                (coverage * 0.34) +
                (min(meanEnergy, 1.0) * 0.16) +
                (min(localPeak, 1.0) * 0.10) +
                (min(motionLevel, 1.0) * 0.12) +
                transcriptBoost

            if startsOnSpeech {
                score += 0.08
            }

            // Prefer windows with enough spoken content for captions.
            if wordCount >= 8 {
                score += 0.05
            }

            scored.append(
                ShortCandidate(
                    id: UUID(),
                    startTime: startTime,
                    duration: target,
                    score: min(score, 1.0),
                    speechCoverage: coverage,
                    motionLevel: min(motionLevel, 1.0),
                    startsOnSpeech: startsOnSpeech,
                    quote: quote
                )
            )

            index += step
        }

        return selectNonOverlapping(from: scored, limit: maximumResults)
    }

    /// Phrases that tend to hold attention in Shorts get a scoring bump.
    private static func transcriptBoost(for quote: String) -> Double {
        guard !quote.isEmpty else { return 0 }

        let lower = quote.lowercased()
        let hooks = [
            "look at", "check this", "check out", "you need", "wait until",
            "watch this", "oh my", "no way", "worth it", "don't buy",
            "buy this", "so creepy", "so cool", "right here", "found this"
        ]

        if hooks.contains(where: { lower.contains($0) }) {
            return 0.18
        }

        if quote.split(separator: " ").count >= 12 {
            return 0.10
        }

        return 0.04
    }

    private static func selectNonOverlapping(
        from candidates: [ShortCandidate],
        limit: Int
    ) -> [ShortCandidate] {
        var selected: [ShortCandidate] = []

        for candidate in candidates.sorted(by: { $0.score > $1.score }) {
            guard selected.count < limit else { break }

            let overlaps = selected.contains { chosen in
                candidate.startTime < chosen.endTime + minimumGapSeconds &&
                chosen.startTime < candidate.endTime + minimumGapSeconds
            }

            if !overlaps {
                selected.append(candidate)
            }
        }

        return selected.sorted { $0.startTime < $1.startTime }
    }

    // MARK: - Math helpers

    private static func rootMeanSquare(_ data: Data) -> Float {
        guard data.count >= 2 else { return 0 }

        var sum: Float = 0
        var count = 0

        data.withUnsafeBytes { rawBuffer in
            let samples = rawBuffer.bindMemory(to: Int16.self)
            for sample in samples {
                let normalized = Float(sample) / Float(Int16.max)
                sum += normalized * normalized
                count += 1
            }
        }

        guard count > 0 else { return 0 }
        return sqrt(sum / Float(count))
    }

    private static func luminanceHistogram(_ image: CGImage) -> [Int] {
        let width = image.width
        let height = image.height
        let bucketCount = 32

        guard width > 0, height > 0 else {
            return Array(repeating: 0, count: bucketCount)
        }

        var pixels = [UInt8](repeating: 0, count: width * height)
        let colorSpace = CGColorSpaceCreateDeviceGray()

        guard let context = CGContext(
            data: &pixels,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: width,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.none.rawValue
        ) else {
            return Array(repeating: 0, count: bucketCount)
        }

        context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))

        var histogram = Array(repeating: 0, count: bucketCount)
        for pixel in pixels {
            histogram[Int(pixel) * bucketCount / 256] += 1
        }

        return histogram
    }

    private static func histogramDifference(_ first: [Int], _ second: [Int]) -> Double {
        let total = max(first.reduce(0, +), 1)
        var difference = 0

        for index in 0..<min(first.count, second.count) {
            difference += abs(first[index] - second[index])
        }

        return Double(difference) / Double(total * 2)
    }
}
