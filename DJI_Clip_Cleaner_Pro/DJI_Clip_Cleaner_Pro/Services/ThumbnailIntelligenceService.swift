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

    var formattedTime: String {
        let total = Int(timeSeconds.rounded())
        return String(format: "%d:%02d", total / 60, total % 60)
    }

    var rankLabel: String {
        switch rank {
        case 1:
            return "Top Thumbnail"
        case 2:
            return "Second"
        case 3:
            return "Third"
        case 4:
            return "Fourth"
        case 5:
            return "Fifth"
        default:
            return "Option \(rank)"
        }
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

    private static let sampleCount = 30
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

        var scored: [(time: TimeInterval, score: Double, reasons: [String])] = []
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

            let analysis = analyze(image: image, previousPixels: previousPixels)
            previousPixels = analysis.pixels

            // Near-duplicates of a previous frame rarely help the ranking.
            if analysis.similarityToPrevious > 0.92 {
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
                    reasons: reasons
                )
            )
        }

        guard !scored.isEmpty else {
            throw ServiceError.noFrames
        }

        let ranked = scored
            .sorted { $0.score > $1.score }
            .prefix(topCount)

        // Only the frames that actually won get decoded at full quality.
        let full = AVAssetImageGenerator(asset: asset)
        full.appliesPreferredTrackTransform = true
        full.maximumSize = CGSize(width: 1_280, height: 720)
        full.requestedTimeToleranceBefore = CMTime(seconds: 0.15, preferredTimescale: 600)
        full.requestedTimeToleranceAfter = CMTime(seconds: 0.15, preferredTimescale: 600)

        var results: [RankedThumbnailCandidate] = []

        for (offset, item) in ranked.enumerated() {
            let rank = offset + 1
            let time = CMTime(seconds: item.time, preferredTimescale: 600)

            guard let frame = try? await capture(generator: full, at: time) else {
                continue
            }

            let outputURL = outputFolder.appendingPathComponent(
                "ranked_\(rank)_\(Int(item.time.rounded()))s.jpg"
            )

            try await ThumbnailService.generate(
                from: frame,
                title: thumbnailText,
                brand: brand,
                outputURL: outputURL
            )

            results.append(
                RankedThumbnailCandidate(
                    id: UUID(),
                    rank: rank,
                    score: Int((item.score * 100).rounded()),
                    timeSeconds: item.time,
                    reasons: item.reasons,
                    imagePath: outputURL.path
                )
            )
        }

        guard !results.isEmpty else {
            throw ServiceError.noFrames
        }

        return results
    }

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
    }

    private static func analyze(
        image: CGImage,
        previousPixels: [UInt8]?
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

        var score =
            (sharpness * 0.34) +
            (contrast * 0.22) +
            (exposure * 0.16) +
            (face.score * 0.28)

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
        if face.count > 0 {
            reasons.append(face.count == 1 ? "clear face" : "\(face.count) faces")
            if face.centered {
                reasons.append("well framed")
                score += 0.04
            }
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
            similarityToPrevious: similarity
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

    private static func faceScore(image: CGImage) -> (score: Double, count: Int, centered: Bool) {
        let request = VNDetectFaceRectanglesRequest()
        let handler = VNImageRequestHandler(cgImage: image, options: [:])

        do {
            try handler.perform([request])
        } catch {
            return (0.15, 0, false)
        }

        let faces = request.results ?? []
        guard !faces.isEmpty else {
            return (0.18, 0, false)
        }

        let largest = faces.max(by: {
            ($0.boundingBox.width * $0.boundingBox.height) <
                ($1.boundingBox.width * $1.boundingBox.height)
        })

        let area = (largest?.boundingBox.width ?? 0) * (largest?.boundingBox.height ?? 0)
        let centerX = largest?.boundingBox.midX ?? 0.5
        let centerY = largest?.boundingBox.midY ?? 0.5
        let centered = abs(centerX - 0.5) < 0.22 && abs(centerY - 0.55) < 0.28

        let sizeScore = min(area / 0.18, 1.0)
        let score = 0.45 + (sizeScore * 0.45) + (centered ? 0.1 : 0)

        return (min(score, 1.0), faces.count, centered)
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
