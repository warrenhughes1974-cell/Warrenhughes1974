import AVFoundation
import Foundation

struct SpeechAnalysis: Sendable {
    let talkingPercent: Double
    let hasSpeech: Bool
    let summary: String
}

enum SpeechAnalyzer {
  private static let sampleWindowSeconds = 0.5
  private static let minimumRMS: Float = 0.012

  static func analyze(videoURL: URL) async -> SpeechAnalysis {
    let asset = AVURLAsset(url: videoURL)

  guard let audioTrack = try? await asset.loadTracks(withMediaType: .audio).first else {
      return SpeechAnalysis(
        talkingPercent: 0,
        hasSpeech: false,
        summary: "No audio track"
      )
    }

    guard let reader = try? AVAssetReader(asset: asset) else {
      return SpeechAnalysis(
        talkingPercent: 0,
        hasSpeech: false,
        summary: "Unreadable audio"
      )
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

    guard reader.canAdd(output) else {
      return SpeechAnalysis(
        talkingPercent: 0,
        hasSpeech: false,
        summary: "Audio decode failed"
      )
    }

    reader.add(output)
    guard reader.startReading() else {
      return SpeechAnalysis(
        talkingPercent: 0,
        hasSpeech: false,
        summary: "Audio read failed"
      )
    }

    var activeWindows = 0
    var totalWindows = 0
    var sampleBuffer = Data()

    let bytesPerWindow = Int(16_000 * sampleWindowSeconds) * 2

    while reader.status == .reading {
      guard let sample = output.copyNextSampleBuffer(),
            let block = CMSampleBufferGetDataBuffer(sample) else {
        continue
      }

      let length = CMBlockBufferGetDataLength(block)
      var chunk = Data(count: length)
      chunk.withUnsafeMutableBytes { pointer in
        guard let base = pointer.baseAddress else { return }
        CMBlockBufferCopyDataBytes(block, atOffset: 0, dataLength: length, destination: base)
      }

      sampleBuffer.append(chunk)

      while sampleBuffer.count >= bytesPerWindow {
        let window = sampleBuffer.prefix(bytesPerWindow)
        sampleBuffer.removeFirst(bytesPerWindow)

        let rms = rootMeanSquare(window)
        totalWindows += 1
        if rms >= minimumRMS {
          activeWindows += 1
        }
      }
    }

    guard totalWindows > 0 else {
      return SpeechAnalysis(
        talkingPercent: 0,
        hasSpeech: false,
        summary: "Silent"
      )
    }

    let percent = (Double(activeWindows) / Double(totalWindows)) * 100
    let rounded = percent.rounded()

    if rounded < 5 {
      return SpeechAnalysis(
        talkingPercent: rounded,
        hasSpeech: false,
        summary: "Silent"
      )
    }

    return SpeechAnalysis(
      talkingPercent: rounded,
      hasSpeech: true,
      summary: "Talking \(Int(rounded))%"
    )
  }

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
}
