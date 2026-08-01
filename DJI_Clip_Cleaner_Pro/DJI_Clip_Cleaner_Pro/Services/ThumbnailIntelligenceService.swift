import AVFoundation
import Foundation
import Vision

#if canImport(AppKit)
import AppKit
#endif

struct RankedThumbnailCandidate: Identifiable, Sendable {
    let id: UUID
    let rank: Int
    let score: Int
    let timeSeconds: TimeInterval
    let reasons: [String]
    let imagePath: String
    let isStoryMatch: Bool

    var formattedTime: String {
        let total = Int(timeSeconds.rounded())
        return String(format: "%d:%02d", total / 60, total % 60)
    }

    var rankLabel: String {
        if isStoryMatch {
            return rank == 1 ? "Top Story Match" : "Story Match \(rank)"
        }
        return rank == 1 ? "Top Sharp Option" : "Sharp Alternative \(rank)"
    }
}

enum ThumbnailIntelligenceService {
    enum ServiceError: LocalizedError {
        case unreadable
        case noFrames
        case writeFailed

        var errorDescription: String? {
            switch self {
            case .unreadable:
                return "Could not read the video for thumbnail intelligence."
            case .noFrames:
                return "Could not find usable thumbnail frames in this video."
            case .writeFailed:
                return "Could not save ranked thumbnail previews."
            }
        }
    }

    private static let sampleCount = 60
    private static let topCount = 8

    /// Samples ~30 frames across the video, scores them, and returns the top
    /// branded JPEG previews the user can choose from.
    ///
    /// `progress` reports (framesScanned, totalFrames) so a long scan does not
    /// look like the app has stalled. It is MainActor-isolated so the YouTube
    /// Prep UI can update a progress bar without Sendable/self-capture errors.
    static func rankFrames(
        videoURL: URL,
        thumbnailText: String,
        brand: BrandSettingsValues,
        outputFolder: URL,
        storyBrief: StoryBrief? = nil,
        storySummary: String = "",
        openAIAPIKey: String? = nil,
        useVisionRerank: Bool = false,
        openAIModel: String = "gpt-4o-mini",
        cloudProvider: CloudAIProvider = .openAI,
        progress: (@MainActor (Int, Int) -> Void)? = nil
    ) async throws -> [RankedThumbnailCandidate] {
        let asset = AVURLAsset(url: videoURL)
        let durationValue = try await asset.load(.duration)
        let duration = CMTimeGetSeconds(durationValue)

        guard duration.isFinite, duration > 1.5 else {
            throw ServiceError.unreadable
        }

        try FileManager.default.createDirectory(
            at: outputFolder,
            withIntermediateDirectories: true
        )

        // Scoring only needs enough pixels to judge sharpness, contrast, and
        // faces. Decoding the scan at preview size keeps 30 seeks through a long
        // 4K export from taking minutes, and keeps 30 frames out of memory.
        let scout = AVAssetImageGenerator(asset: asset)
        scout.appliesPreferredTrackTransform = true
        scout.maximumSize = CGSize(width: 640, height: 360)
        scout.requestedTimeToleranceBefore = CMTime(seconds: 1.0, preferredTimescale: 600)
        scout.requestedTimeToleranceAfter = CMTime(seconds: 1.0, preferredTimescale: 600)

        // Skip intros and outros. Cap used to be 4s, which left house outros /
        // bag-claim endings inside long videos — sample the middle story instead.
        let leadSkip = max(min(duration * 0.12, 45.0), min(20.0, duration * 0.2))
        let trailSkip = max(min(duration * 0.18, 60.0), min(30.0, duration * 0.25))
        let usableStart = min(leadSkip, duration * 0.3)
        let usableEnd = max(duration - trailSkip, usableStart + 1.0)
        let span = usableEnd - usableStart
        let visualTargets = storyBrief?.visualTargets ?? []

        var scored: [
            (
                time: TimeInterval,
                score: Double,
                storyMatch: Double,
                reasons: [String]
            )
        ] = []
        var previousPixels: [UInt8]?

        for index in 0..<sampleCount {
            if let progress {
                await progress(index + 1, sampleCount)
            }

            let fraction = sampleCount == 1 ? 0.5 : Double(index) / Double(sampleCount - 1)
            let seconds = usableStart + (span * fraction)
            let time = CMTime(seconds: seconds, preferredTimescale: 600)

            guard let image = try? await capture(generator: scout, at: time) else {
                continue
            }

            let analysis = analyze(
                image: image,
                previousPixels: previousPixels,
                visualTargets: visualTargets,
                domain: storyBrief?.domain
            )
            previousPixels = analysis.pixels

            // Hard reject mushy / motion-blur frames.
            if analysis.sharpness < 0.45 {
                continue
            }

            // Near-duplicates of a previous frame rarely help the ranking.
            if analysis.similarityToPrevious > 0.92 {
                continue
            }

            // Idiot-selfie close-ups — face fills the frame.
            if analysis.faceAreaRatio > 0.32 {
                continue
            }

            // A food/beverage close-up is not an alternate for an airport-delay
            // story. Preserve sharp alternatives, but remove clear conflicts.
            if analysis.storyConflict {
                continue
            }

            var score = analysis.score
            var reasons = analysis.reasons
            let position = seconds / duration

            // Soft-penalize leftover early/late frames that still sneak in.
            if position > 0.82 {
                score *= 0.55
                reasons.append("late in video")
            } else if position < 0.12 {
                score *= 0.75
            }

            scored.append(
                (
                    time: seconds,
                    score: score,
                    storyMatch: analysis.storyMatch,
                    reasons: reasons
                )
            )
        }

        guard !scored.isEmpty else {
            throw ServiceError.noFrames
        }

        // Story matches first, then additional sharp choices. Do not remove the
        // user's ability to pick an alternate frame.
        let ordered = scored.sorted { lhs, rhs in
            let leftMatch = lhs.storyMatch >= 0.18
            let rightMatch = rhs.storyMatch >= 0.18
            if leftMatch != rightMatch {
                return leftMatch && !rightMatch
            }
            return lhs.score > rhs.score
        }

        // Avoid nearly identical moments from a static shot filling the picker.
        let minimumSeparation = max(duration / 90, 4.0)
        var ranked: [
            (
                time: TimeInterval,
                score: Double,
                storyMatch: Double,
                reasons: [String]
            )
        ] = []
        for candidate in ordered {
            guard ranked.allSatisfy({
                abs($0.time - candidate.time) >= minimumSeparation
            }) else { continue }
            ranked.append(candidate)
            if ranked.count >= topCount { break }
        }

        // Decode winners larger than 1280 so punch-up/downscale stays sharp.
        let full = AVAssetImageGenerator(asset: asset)
        full.appliesPreferredTrackTransform = true
        full.maximumSize = CGSize(width: 1_920, height: 1_080)
        full.requestedTimeToleranceBefore = CMTime(seconds: 0.15, preferredTimescale: 600)
        full.requestedTimeToleranceAfter = CMTime(seconds: 0.15, preferredTimescale: 600)

        // Optional OpenAI Vision rerank + overlay suggestions on the local top picks.
        var orderedForRender = ranked
        var overlayByIndex: [Int: String] = [:]
        var visionReasonsByIndex: [Int: String] = [:]

        if useVisionRerank,
           let apiKey = openAIAPIKey,
           !apiKey.isEmpty,
           !ranked.isEmpty {
            if let progress {
                await progress(sampleCount, sampleCount)
            }

            var jpegPayloads: [Data] = []
            var validLocal: [
                (
                    time: TimeInterval,
                    score: Double,
                    storyMatch: Double,
                    reasons: [String]
                )
            ] = []

            for item in ranked.prefix(6) {
                let time = CMTime(seconds: item.time, preferredTimescale: 600)
                guard let frame = try? await capture(generator: scout, at: time),
                      let jpeg = jpegData(from: frame, quality: 0.72) else {
                    continue
                }
                jpegPayloads.append(jpeg)
                validLocal.append(item)
            }

            if jpegPayloads.count >= 2 {
                do {
                    let plan = try await CloudAIClient.rankThumbnailFrames(
                        jpegImages: jpegPayloads,
                        storySummary: storySummary.isEmpty
                            ? (storyBrief?.summary ?? thumbnailText)
                            : storySummary,
                        domain: storyBrief?.domain.displayName ?? "General",
                        currentOverlay: thumbnailText,
                        provider: cloudProvider,
                        model: openAIModel,
                        apiKey: apiKey
                    )

                    var remapped: [
                        (
                            time: TimeInterval,
                            score: Double,
                            storyMatch: Double,
                            reasons: [String]
                        )
                    ] = []
                    for (pickOffset, pick) in plan.picks.enumerated() {
                        guard pick.localIndex >= 0,
                              pick.localIndex < validLocal.count else { continue }
                        let source = validLocal[pick.localIndex]
                        var reasons = source.reasons
                        if !pick.reason.isEmpty {
                            reasons = ["AI: \(pick.reason)"] + reasons
                        }
                        remapped.append(
                            (
                                time: source.time,
                                score: source.score,
                                storyMatch: source.storyMatch,
                                reasons: reasons
                            )
                        )
                        if !pick.overlayText.isEmpty {
                            overlayByIndex[pickOffset] = pick.overlayText
                        }
                        visionReasonsByIndex[pickOffset] = pick.reason
                    }
                    if remapped.count == validLocal.count {
                        // Keep any local winners Vision didn't see (beyond top 6).
                        let keptTimes = Set(remapped.map(\.time))
                        for leftover in ranked where !keptTimes.contains(leftover.time) {
                            remapped.append(leftover)
                        }
                        orderedForRender = remapped
                    }
                } catch {
                    // Vision is a boost, not a hard dependency.
                }
            }
        }

        var results: [RankedThumbnailCandidate] = []

        for (offset, item) in orderedForRender.enumerated() {
            let rank = offset + 1
            let time = CMTime(seconds: item.time, preferredTimescale: 600)

            guard let frame = try? await capture(generator: full, at: time) else {
                continue
            }

            let outputURL = outputFolder.appendingPathComponent(
                "ranked_\(rank)_\(Int(item.time.rounded()))s.jpg"
            )

            let overlay = overlayByIndex[offset]?.trimmingCharacters(in: .whitespacesAndNewlines)
            let titleForFrame = (overlay?.isEmpty == false) ? overlay! : thumbnailText

            try await ThumbnailService.generate(
                from: frame,
                title: titleForFrame,
                brand: brand,
                outputURL: outputURL
            )

            var reasons = item.reasons
            if let visionReason = visionReasonsByIndex[offset], !visionReason.isEmpty,
               !reasons.contains(where: { $0.hasPrefix("AI:") }) {
                reasons.insert("AI: \(visionReason)", at: 0)
            }
            if overlay?.isEmpty == false {
                reasons.insert("Overlay: \(titleForFrame)", at: 0)
            }

            results.append(
                RankedThumbnailCandidate(
                    id: UUID(),
                    rank: rank,
                    score: Int((item.score * 100).rounded()),
                    timeSeconds: item.time,
                    reasons: reasons,
                    imagePath: outputURL.path,
                    isStoryMatch: item.storyMatch >= 0.18
                )
            )
        }

        guard !results.isEmpty else {
            throw ServiceError.noFrames
        }

        return results
    }

    #if canImport(AppKit)
    private static func jpegData(from image: CGImage, quality: CGFloat) -> Data? {
        let nsImage = NSImage(
            cgImage: image,
            size: NSSize(width: image.width, height: image.height)
        )
        guard let tiff = nsImage.tiffRepresentation,
              let rep = NSBitmapImageRep(data: tiff) else {
            return nil
        }
        return rep.representation(
            using: .jpeg,
            properties: [.compressionFactor: quality]
        )
    }
    #endif

    // MARK: - Capture

    private static func capture(
        generator: AVAssetImageGenerator,
        at time: CMTime
    ) async throws -> CGImage {
        try await generator.image(at: time).image
    }

    // MARK: - Scoring

    private struct FrameAnalysis {
        let score: Double
        let reasons: [String]
        let pixels: [UInt8]
        let similarityToPrevious: Double
        let sharpness: Double
        let faceAreaRatio: Double
        let storyMatch: Double
        let storyConflict: Bool
    }

    private static func analyze(
        image: CGImage,
        previousPixels: [UInt8]?,
        visualTargets: [String] = [],
        domain: StoryDomain? = nil
    ) -> FrameAnalysis {
        let width = min(image.width, 320)
        let height = max(Int(Double(width) * Double(image.height) / Double(max(image.width, 1))), 1)
        var pixels = [UInt8](repeating: 0, count: width * height)

        let colorSpace = CGColorSpaceCreateDeviceGray()
        pixels.withUnsafeMutableBytes { buffer in
            guard let base = buffer.baseAddress,
                  let context = CGContext(
                    data: base,
                    width: width,
                    height: height,
                    bitsPerComponent: 8,
                    bytesPerRow: width,
                    space: colorSpace,
                    bitmapInfo: CGImageAlphaInfo.none.rawValue
                  ) else {
                return
            }

            context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
        }

        let sharpness = laplacianVariance(pixels, width: width, height: height)
        let contrast = contrastScore(pixels)
        let exposure = exposureScore(pixels)
        let face = faceScore(image: image)
        let storyMatch = storyMatchScore(image: image, targets: visualTargets)

        // Story match + sharpness first. Faces are a light bonus only when they
        // do not dominate the frame — never the whole strategy.
        var score =
            (sharpness * 0.34) +
            (contrast * 0.18) +
            (exposure * 0.12) +
            (storyMatch.score * 0.28) +
            (face.score * 0.08)

        var reasons: [String] = []

        if sharpness >= 0.7 {
            reasons.append("sharp")
        }
        if contrast >= 0.65 {
            reasons.append("high contrast")
        }
        if exposure >= 0.7 {
            reasons.append("good lighting")
        }
        if storyMatch.score >= 0.45 {
            reasons.append(contentsOf: storyMatch.reasons)
        }

        // Soft face presence is fine; giant selfie faces already hard-rejected.
        if face.count > 0, face.areaRatio < 0.18 {
            reasons.append(face.count == 1 ? "person in scene" : "\(face.count) people")
            if face.centered {
                score += 0.02
            }
        } else if face.areaRatio >= 0.18 {
            score *= 0.7
            reasons.append("face too close")
        }

        // Delay stories without any airport/plane cue get a soft demotion so
        // random shelves don't win by sharpness alone.
        if domain == .travelDelay, storyMatch.score < 0.2 {
            score *= 0.82
        }

        if reasons.isEmpty {
            reasons.append("usable frame")
        }

        let similarity: Double
        if let previousPixels, previousPixels.count == pixels.count {
            similarity = pixelSimilarity(previousPixels, pixels)
        } else {
            similarity = 0
        }

        return FrameAnalysis(
            score: min(max(score, 0), 1),
            reasons: reasons,
            pixels: pixels,
            similarityToPrevious: similarity,
            sharpness: sharpness,
            faceAreaRatio: face.areaRatio,
            storyMatch: storyMatch.score,
            storyConflict: domain == .travelDelay
                && storyMatch.conflictsWithTravel
                && storyMatch.score < 0.18
        )
    }

    private static func laplacianVariance(
        _ pixels: [UInt8],
        width: Int,
        height: Int
    ) -> Double {
        guard width > 2, height > 2 else { return 0 }

        var sum: Double = 0
        var sumSquares: Double = 0
        var count = 0

        for y in 1..<(height - 1) {
            for x in 1..<(width - 1) {
                let center = Int(pixels[y * width + x])
                let up = Int(pixels[(y - 1) * width + x])
                let down = Int(pixels[(y + 1) * width + x])
                let left = Int(pixels[y * width + (x - 1)])
                let right = Int(pixels[y * width + (x + 1)])
                let laplacian = Double((-4 * center) + up + down + left + right)
                sum += laplacian
                sumSquares += laplacian * laplacian
                count += 1
            }
        }

        guard count > 0 else { return 0 }

        let mean = sum / Double(count)
        let variance = max((sumSquares / Double(count)) - (mean * mean), 0)

        // Empirically maps typical phone/DJI frames into a 0...1 band.
        return min(variance / 1_800.0, 1.0)
    }

    private static func contrastScore(_ pixels: [UInt8]) -> Double {
        guard !pixels.isEmpty else { return 0 }

        let mean = Double(pixels.reduce(0) { $0 + Int($1) }) / Double(pixels.count)
        let variance = pixels.reduce(0.0) { partial, value in
            let delta = Double(value) - mean
            return partial + (delta * delta)
        } / Double(pixels.count)

        return min(sqrt(variance) / 70.0, 1.0)
    }

    private static func exposureScore(_ pixels: [UInt8]) -> Double {
        guard !pixels.isEmpty else { return 0 }

        let mean = Double(pixels.reduce(0) { $0 + Int($1) }) / Double(pixels.count)

        // Reward midtones; punish crushed blacks and blown highlights.
        let distance = abs(mean - 128.0) / 128.0
        return max(1.0 - distance, 0)
    }

    private static func faceScore(image: CGImage) -> (score: Double, count: Int, centered: Bool, areaRatio: Double) {
        let request = VNDetectFaceRectanglesRequest()
        let handler = VNImageRequestHandler(cgImage: image, options: [:])

        do {
            try handler.perform([request])
        } catch {
            return (0.15, 0, false, 0)
        }

        let faces = request.results ?? []
        guard !faces.isEmpty else {
            return (0.18, 0, false, 0)
        }

        let largest = faces.max(by: {
            ($0.boundingBox.width * $0.boundingBox.height) <
                ($1.boundingBox.width * $1.boundingBox.height)
        })

        let area = (largest?.boundingBox.width ?? 0) * (largest?.boundingBox.height ?? 0)
        let centerX = largest?.boundingBox.midX ?? 0.5
        let centerY = largest?.boundingBox.midY ?? 0.5
        let centered = abs(centerX - 0.5) < 0.22 && abs(centerY - 0.55) < 0.28

        // Medium face in scene = mild bonus. Giant close-up = low score.
        let sizeScore: Double
        if area > 0.28 {
            sizeScore = 0.15
        } else if area > 0.12 {
            sizeScore = 0.45
        } else {
            sizeScore = min(area / 0.12, 1.0) * 0.7
        }
        let score = 0.25 + (sizeScore * 0.5) + (centered ? 0.05 : 0)

        return (min(score, 1.0), faces.count, centered, area)
    }

    /// OCR + image classification against story visual targets (plane, gate, etc.).
    private static func storyMatchScore(
        image: CGImage,
        targets: [String]
    ) -> (score: Double, reasons: [String], conflictsWithTravel: Bool) {
        guard !targets.isEmpty else {
            return (0, [], false)
        }

        let loweredTargets = targets.map { $0.lowercased() }
        var hits: [String] = []
        var score = 0.0

        let textRequest = VNRecognizeTextRequest()
        textRequest.recognitionLevel = .fast
        textRequest.usesLanguageCorrection = false

        let classifyRequest = VNClassifyImageRequest()
        let handler = VNImageRequestHandler(cgImage: image, options: [:])

        do {
            try handler.perform([textRequest, classifyRequest])
        } catch {
            return (0.15, [], false)
        }

        let ocrText = (textRequest.results ?? [])
            .compactMap { $0.topCandidates(1).first?.string.lowercased() }
            .joined(separator: " ")

        for target in loweredTargets {
            if !target.isEmpty, ocrText.contains(target) {
                hits.append(target)
                score += 0.22
            }
        }

        let classifications = (classifyRequest.results ?? [])
            .prefix(8)
            .map {
                (
                    identifier: $0.identifier.lowercased(),
                    confidence: $0.confidence
                )
            }

        for classification in classifications where classification.confidence >= 0.2 {
            let identifier = classification.identifier
            for target in loweredTargets where identifier.contains(target) || target.contains(identifier) {
                if !hits.contains(target) {
                    hits.append(target)
                }
                score += 0.18
            }
        }

        // Common Vision labels for airport/plane scenes even when targets are short.
        let travelLabels = ["airplane", "aircraft", "airport", "jet", "airliner", "terminal"]
        if loweredTargets.contains(where: { travelLabels.contains($0) }) {
            for label in travelLabels where classifications.contains(where: {
                $0.confidence >= 0.2 && $0.identifier.contains(label)
            }) {
                if !hits.contains(label) {
                    hits.append(label)
                }
                score += 0.2
            }
        }

        var reasons: [String] = []
        if !hits.isEmpty {
            reasons.append("matches story (\(hits.prefix(2).joined(separator: ", ")))")
        }

        let travelConflicts = [
            "food", "dish", "salad", "vegetable", "beverage", "bottle",
            "soft drink", "grocery", "meal"
        ]
        let conflictsWithTravel = classifications.contains { classification in
            classification.confidence >= 0.45
                && travelConflicts.contains {
                    classification.identifier.contains($0)
                }
        }

        return (min(score, 1.0), reasons, conflictsWithTravel)
    }

    private static func pixelSimilarity(_ first: [UInt8], _ second: [UInt8]) -> Double {
        let step = max(first.count / 2_000, 1)
        var totalDiff = 0
        var samples = 0
        var index = 0

        while index < first.count {
            totalDiff += abs(Int(first[index]) - Int(second[index]))
            samples += 1
            index += step
        }

        guard samples > 0 else { return 0 }
        let averageDiff = Double(totalDiff) / Double(samples) / 255.0
        return max(1.0 - averageDiff, 0)
    }
}
