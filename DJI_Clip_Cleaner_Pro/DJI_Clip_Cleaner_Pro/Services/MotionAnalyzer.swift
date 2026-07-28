import AVFoundation
import Foundation

struct MotionAnalysis: Sendable {
    let motionPercent: Double
    let isStatic: Bool
    let summary: String
}

enum MotionAnalyzer {
  private static let frameIntervalSeconds = 1.0
  private static let motionThreshold = 0.08

  static func analyze(videoURL: URL) async -> MotionAnalysis {
    let asset = AVURLAsset(url: videoURL)
    let generator = AVAssetImageGenerator(asset: asset)
    generator.appliesPreferredTrackTransform = true
    generator.maximumSize = CGSize(width: 320, height: 180)
    generator.requestedTimeToleranceBefore = .zero
    generator.requestedTimeToleranceAfter = .zero

    let duration: Double
    do {
      let loadedDuration = try await asset.load(.duration)
      duration = CMTimeGetSeconds(loadedDuration)
    } catch {
      return MotionAnalysis(motionPercent: 0, isStatic: true, summary: "Unreadable")
    }

    guard duration.isFinite, duration > 0 else {
      return MotionAnalysis(motionPercent: 0, isStatic: true, summary: "Unreadable")
    }

    let frameCount = max(Int(duration / frameIntervalSeconds), 1)
    var previousHistogram: [Int]? = nil
    var movingFrames = 0
    var sampledFrames = 0

    for index in 0..<frameCount {
      let seconds = min(Double(index) * frameIntervalSeconds, max(duration - 0.1, 0))
      let time = CMTime(seconds: seconds, preferredTimescale: 600)

      guard let cgImage = try? generator.copyCGImage(at: time, actualTime: nil) else {
        continue
      }

      let histogram = histogramForImage(cgImage)
      sampledFrames += 1

      if let previousHistogram {
        let difference = histogramDifference(previousHistogram, histogram)
        if difference >= motionThreshold {
          movingFrames += 1
        }
      }

      previousHistogram = histogram
    }

    guard sampledFrames > 1 else {
      return MotionAnalysis(motionPercent: 0, isStatic: true, summary: "Static")
    }

    let percent = (Double(movingFrames) / Double(sampledFrames - 1)) * 100
    let rounded = percent.rounded()

    if rounded < 10 {
      return MotionAnalysis(
        motionPercent: rounded,
        isStatic: true,
        summary: "Static"
      )
    }

    return MotionAnalysis(
      motionPercent: rounded,
      isStatic: false,
      summary: "Moving \(Int(rounded))%"
    )
  }

  private static func histogramForImage(_ image: CGImage) -> [Int] {
    let width = 16
    let height = 16
    let colorSpace = CGColorSpaceCreateDeviceRGB()
    var pixels = [UInt8](repeating: 0, count: width * height * 4)

    guard let context = CGContext(
      data: &pixels,
      width: width,
      height: height,
      bitsPerComponent: 8,
      bytesPerRow: width * 4,
      space: colorSpace,
      bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
    ) else {
      return Array(repeating: 0, count: 16)
    }

    context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))

    var bins = Array(repeating: 0, count: 16)
    for index in stride(from: 0, to: pixels.count, by: 4) {
      let red = Int(pixels[index])
      let green = Int(pixels[index + 1])
      let blue = Int(pixels[index + 2])
      let brightness = (red + green + blue) / 3
      let bin = min(brightness / 16, 15)
      bins[bin] += 1
    }

    return bins
  }

  private static func histogramDifference(_ lhs: [Int], _ rhs: [Int]) -> Double {
    let totalLHS = max(lhs.reduce(0, +), 1)
    let totalRHS = max(rhs.reduce(0, +), 1)

    var difference = 0.0
    for index in lhs.indices {
      let left = Double(lhs[index]) / Double(totalLHS)
      let right = Double(rhs[index]) / Double(totalRHS)
      difference += abs(left - right)
    }

    return difference / 2.0
  }
}
