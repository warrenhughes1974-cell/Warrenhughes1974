import AVFoundation
import Foundation
import Speech

struct TranscriptSegment: Identifiable, Sendable, Equatable {
    let id: UUID
    let text: String
    let startTime: TimeInterval
    let duration: TimeInterval

    var endTime: TimeInterval {
        startTime + duration
    }

    init(
        id: UUID = UUID(),
        text: String,
        startTime: TimeInterval,
        duration: TimeInterval
    ) {
        self.id = id
        self.text = text
        self.startTime = startTime
        self.duration = duration
    }
}

struct Transcript: Sendable, Equatable {
    let fullText: String
    let segments: [TranscriptSegment]
    let languageCode: String
    let usedOnDevice: Bool

    var isEmpty: Bool {
        fullText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    func segments(
        overlapping start: TimeInterval,
        duration: TimeInterval
    ) -> [TranscriptSegment] {
        let end = start + duration

        return segments.filter { segment in
            segment.startTime < end && segment.endTime > start
        }
    }

    func text(
        overlapping start: TimeInterval,
        duration: TimeInterval
    ) -> String {
        segments(overlapping: start, duration: duration)
            .map(\.text)
            .joined(separator: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// Phrase groups suitable for burned-in Shorts captions.
    func captionCues(
        overlapping start: TimeInterval,
        duration: TimeInterval,
        wordsPerCue: Int = 4
    ) -> [(start: TimeInterval, end: TimeInterval, text: String)] {
        let windowEnd = start + duration
        let relevant = segments(overlapping: start, duration: duration)
        guard !relevant.isEmpty else { return [] }

        var cues: [(start: TimeInterval, end: TimeInterval, text: String)] = []
        var buffer: [TranscriptSegment] = []

        func flush() {
            guard !buffer.isEmpty else { return }

            let cueStart = max(buffer.first!.startTime - start, 0)
            let cueEnd = min(buffer.last!.endTime - start, duration)
            let text = buffer.map(\.text).joined(separator: " ")

            if cueEnd > cueStart, !text.isEmpty {
                cues.append((cueStart, cueEnd, text.uppercased()))
            }

            buffer = []
        }

        for segment in relevant {
            guard segment.startTime < windowEnd else { break }
            buffer.append(segment)

            if buffer.count >= wordsPerCue {
                flush()
            }
        }

        flush()
        return cues
    }
}

struct TranscriptChapter: Sendable {
    let startTime: TimeInterval
    let title: String

    var formattedLine: String {
        "\(TranscriptChapter.timecode(startTime)) \(title)"
    }

    static func timecode(_ seconds: TimeInterval) -> String {
        let total = max(Int(seconds.rounded()), 0)
        let hours = total / 3_600
        let minutes = (total % 3_600) / 60
        let secs = total % 60

        if hours > 0 {
            return String(format: "%d:%02d:%02d", hours, minutes, secs)
        }

        return String(format: "%d:%02d", minutes, secs)
    }
}

enum TranscriptionService {
    enum ServiceError: LocalizedError {
        case notAuthorized
        case recognizerUnavailable
        case audioExtractFailed
        case ffmpegMissing
        case emptyResult
        case recognitionFailed(String)

        var errorDescription: String? {
            switch self {
            case .notAuthorized:
                return "Speech recognition permission was denied. Enable it in System Settings → Privacy & Security → Speech Recognition."
            case .recognizerUnavailable:
                return "Speech recognition is not available. Make sure Siri is enabled and your language supports dictation."
            case .audioExtractFailed:
                return "Could not extract audio from the video for transcription."
            case .ffmpegMissing:
                return "FFmpeg was not found. Install it with: brew install ffmpeg"
            case .emptyResult:
                return "No speech was detected in this video."
            case .recognitionFailed(let message):
                return message
            }
        }
    }

    /// Server recognition caps around one minute. Chunking keeps both modes
    /// reliable on long Filmora exports.
    private static let chunkSeconds: TimeInterval = 50
    private static let chunkOverlapSeconds: TimeInterval = 1.0

    static func requestAuthorization() async -> SFSpeechRecognizerAuthorizationStatus {
        await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status)
            }
        }
    }

    static func transcribe(videoURL: URL) async throws -> Transcript {
        let status = await requestAuthorization()
        guard status == .authorized else {
            throw ServiceError.notAuthorized
        }

        let locale = Locale.current
        guard let recognizer = SFSpeechRecognizer(locale: locale),
              recognizer.isAvailable else {
            throw ServiceError.recognizerUnavailable
        }

        let preferOnDevice = recognizer.supportsOnDeviceRecognition
        let audioURL = try await extractAudio(from: videoURL)
        defer { try? FileManager.default.removeItem(at: audioURL) }

        let asset = AVURLAsset(url: audioURL)
        let duration = CMTimeGetSeconds((try? await asset.load(.duration)) ?? .zero)
        guard duration.isFinite, duration > 0.5 else {
            throw ServiceError.emptyResult
        }

        var collected: [TranscriptSegment] = []
        var cursor: TimeInterval = 0

        while cursor < duration {
            let length = min(chunkSeconds, duration - cursor)
            guard length > 0.4 else { break }

            let chunkURL = try await exportChunk(
                from: audioURL,
                start: cursor,
                duration: length
            )

            defer { try? FileManager.default.removeItem(at: chunkURL) }

            let chunkSegments = try await recognizeFile(
                at: chunkURL,
                recognizer: recognizer,
                preferOnDevice: preferOnDevice,
                timeOffset: cursor
            )

            appendUnique(chunkSegments, onto: &collected)
            cursor += chunkSeconds - chunkOverlapSeconds
        }

        guard !collected.isEmpty else {
            throw ServiceError.emptyResult
        }

        let fullText = collected
            .map(\.text)
            .joined(separator: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)

        return Transcript(
            fullText: fullText,
            segments: collected,
            languageCode: locale.identifier,
            usedOnDevice: preferOnDevice
        )
    }

    /// YouTube needs at least three chapters, each 10 seconds or longer, and a
    /// first chapter at 0:00. A window that contains no nameable subject is
    /// skipped rather than titled with raw dictation.
    static func chapters(
        from transcript: Transcript,
        targetSpacing: TimeInterval? = nil
    ) -> [TranscriptChapter] {
        guard let lastSegment = transcript.segments.last else { return [] }

        let duration = lastSegment.endTime
        guard duration > 120 else { return [] }

        // Roughly ten chapters whatever the runtime, so a 25-minute walkthrough
        // does not produce three dozen of them.
        let spacing = targetSpacing ?? max(60, duration / 10)

        var chapters: [TranscriptChapter] = [
            TranscriptChapter(startTime: 0, title: "Intro")
        ]
        var usedTitles: Set<String> = ["intro"]
        var buffer: [String] = []
        var bufferStart: TimeInterval = 0
        var nextBoundary = spacing

        for segment in transcript.segments {
            if buffer.isEmpty {
                bufferStart = segment.startTime
            }

            buffer.append(segment.text)

            guard segment.endTime >= nextBoundary, buffer.count >= 12 else { continue }

            let windowText = buffer.joined(separator: " ")
            let previousStart = chapters.last?.startTime ?? 0

            // Skip windows that only have a weak single-word subject.
            if let title = TranscriptKeywordService.chapterTitle(from: windowText),
               !usedTitles.contains(title.lowercased()),
               bufferStart - previousStart >= 10 {
                chapters.append(
                    TranscriptChapter(startTime: bufferStart, title: title)
                )
                usedTitles.insert(title.lowercased())
            }

            buffer = []
            nextBoundary = segment.endTime + spacing
        }

        // Below three, YouTube ignores them anyway — better to prompt the user
        // to add their own than to ship a broken chapter list.
        return chapters.count >= 3 ? chapters : []
    }

    static func writeSRT(
        _ transcript: Transcript,
        to url: URL
    ) throws {
        var lines: [String] = []

        for (index, segment) in transcript.segments.enumerated() {
            lines.append("\(index + 1)")
            lines.append(
                "\(srtTimestamp(segment.startTime)) --> \(srtTimestamp(segment.endTime))"
            )
            lines.append(segment.text)
            lines.append("")
        }

        try lines.joined(separator: "\n").write(to: url, atomically: true, encoding: .utf8)
    }

    // MARK: - Recognition

    private static func recognizeFile(
        at url: URL,
        recognizer: SFSpeechRecognizer,
        preferOnDevice: Bool,
        timeOffset: TimeInterval
    ) async throws -> [TranscriptSegment] {
        let request = SFSpeechURLRecognitionRequest(url: url)
        request.shouldReportPartialResults = false
        request.taskHint = .dictation

        if preferOnDevice {
            request.requiresOnDeviceRecognition = true
        }

        return try await withCheckedThrowingContinuation { continuation in
            let lock = NSLock()
            var finished = false

            recognizer.recognitionTask(with: request) { result, error in
                lock.lock()
                defer { lock.unlock() }
                guard !finished else { return }

                if let error {
                    finished = true
                    continuation.resume(
                        throwing: ServiceError.recognitionFailed(error.localizedDescription)
                    )
                    return
                }

                guard let result, result.isFinal else { return }

                finished = true

                let segments = result.bestTranscription.segments.compactMap { segment -> TranscriptSegment? in
                    let text = segment.substring.trimmingCharacters(in: .whitespacesAndNewlines)
                    guard !text.isEmpty else { return nil }

                    return TranscriptSegment(
                        text: text,
                        startTime: timeOffset + segment.timestamp,
                        duration: max(segment.duration, 0.05)
                    )
                }

                continuation.resume(returning: segments)
            }
        }
    }

    // MARK: - Audio extraction

    private static func extractAudio(from videoURL: URL) async throws -> URL {
        guard let ffmpegPath = ProductionPassService.ffmpegPath else {
            throw ServiceError.ffmpegMissing
        }

        let outputURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("HughesClipPrep-Transcript-\(UUID().uuidString).wav")

        let logURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("HughesClipPrep-Transcript-\(UUID().uuidString).log")
        FileManager.default.createFile(atPath: logURL.path, contents: nil)

        let arguments = [
            "-hide_banner",
            "-loglevel",
            "warning",
            "-y",
            "-i",
            videoURL.path,
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            outputURL.path
        ]

        let exitCode = try await runProcess(
            executablePath: ffmpegPath,
            arguments: arguments,
            logURL: logURL
        )

        try? FileManager.default.removeItem(at: logURL)

        guard exitCode == 0,
              FileManager.default.fileExists(atPath: outputURL.path) else {
            try? FileManager.default.removeItem(at: outputURL)
            throw ServiceError.audioExtractFailed
        }

        return outputURL
    }

    private static func exportChunk(
        from audioURL: URL,
        start: TimeInterval,
        duration: TimeInterval
    ) async throws -> URL {
        guard let ffmpegPath = ProductionPassService.ffmpegPath else {
            throw ServiceError.ffmpegMissing
        }

        let outputURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("HughesClipPrep-Chunk-\(UUID().uuidString).wav")

        let logURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("HughesClipPrep-Chunk-\(UUID().uuidString).log")
        FileManager.default.createFile(atPath: logURL.path, contents: nil)

        let arguments = [
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            String(format: "%.3f", start),
            "-i",
            audioURL.path,
            "-t",
            String(format: "%.3f", duration),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            outputURL.path
        ]

        let exitCode = try await runProcess(
            executablePath: ffmpegPath,
            arguments: arguments,
            logURL: logURL
        )

        try? FileManager.default.removeItem(at: logURL)

        guard exitCode == 0,
              FileManager.default.fileExists(atPath: outputURL.path) else {
            try? FileManager.default.removeItem(at: outputURL)
            throw ServiceError.audioExtractFailed
        }

        return outputURL
    }

    private static func runProcess(
        executablePath: String,
        arguments: [String],
        logURL: URL
    ) async throws -> Int32 {
        try await withCheckedThrowingContinuation { continuation in
            let process = Process()
            process.executableURL = URL(fileURLWithPath: executablePath)
            process.arguments = arguments

            guard let outputHandle = try? FileHandle(forWritingTo: logURL) else {
                continuation.resume(throwing: ServiceError.audioExtractFailed)
                return
            }

            process.standardOutput = outputHandle
            process.standardError = outputHandle

            process.terminationHandler = { completed in
                try? outputHandle.close()
                continuation.resume(returning: completed.terminationStatus)
            }

            do {
                try process.run()
            } catch {
                try? outputHandle.close()
                continuation.resume(throwing: error)
            }
        }
    }

    // MARK: - Helpers

    private static func appendUnique(
        _ incoming: [TranscriptSegment],
        onto existing: inout [TranscriptSegment]
    ) {
        for segment in incoming {
            if let last = existing.last,
               abs(last.startTime - segment.startTime) < 0.35,
               last.text.caseInsensitiveCompare(segment.text) == .orderedSame {
                continue
            }

            existing.append(segment)
        }
    }

    private static func srtTimestamp(_ seconds: TimeInterval) -> String {
        let totalMilliseconds = max(Int((seconds * 1_000).rounded()), 0)
        let hours = totalMilliseconds / 3_600_000
        let minutes = (totalMilliseconds % 3_600_000) / 60_000
        let secs = (totalMilliseconds % 60_000) / 1_000
        let millis = totalMilliseconds % 1_000

        return String(format: "%02d:%02d:%02d,%03d", hours, minutes, secs, millis)
    }
}
