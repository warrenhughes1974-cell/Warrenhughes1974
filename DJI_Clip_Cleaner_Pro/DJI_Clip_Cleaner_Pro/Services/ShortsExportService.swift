import Foundation

enum ShortsExportService {
    enum ServiceError: LocalizedError {
        case ffmpegMissing
        case processFailed(Int32, String)

        var errorDescription: String? {
            switch self {
            case .ffmpegMissing:
                return "FFmpeg was not found. Install it with: brew install ffmpeg"
            case .processFailed(let code, let output):
                if output.isEmpty {
                    return "Shorts export failed with exit code \(code)."
                }
                return "Shorts export failed with exit code \(code): \(output)"
            }
        }
    }

    static let outputFolderName = "Shorts"

    static func outputFolder(for videoURL: URL) -> URL {
        videoURL
            .deletingLastPathComponent()
            .appendingPathComponent(outputFolderName, isDirectory: true)
    }

    static func export(
        from videoURL: URL,
        candidate: ShortCandidate,
        index: Int,
        transcript: Transcript? = nil
    ) async throws -> URL {
        guard let ffmpegPath = ProductionPassService.ffmpegPath else {
            throw ServiceError.ffmpegMissing
        }

        let folder = outputFolder(for: videoURL)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)

        let baseName = videoURL.deletingPathExtension().lastPathComponent
        let position = String(format: "%02d", index)
        let sourceSecond = Int(candidate.startTime.rounded())

        // The source timecode keeps the name stable across runs, so re-exporting
        // a different selection cannot overwrite an unrelated clip.
        let outputURL = folder.appendingPathComponent(
            "\(baseName)_short_\(position)_\(sourceSecond)s.mp4"
        )

        let existedBeforeExport = FileManager.default.fileExists(atPath: outputURL.path)

        let logURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("HughesClipPrep-Shorts-\(UUID().uuidString).log")
        FileManager.default.createFile(atPath: logURL.path, contents: nil)

        var assURL: URL?
        if let transcript {
            let cues = transcript.captionCues(
                overlapping: candidate.startTime,
                duration: candidate.duration
            )

            if !cues.isEmpty {
                let captionsURL = FileManager.default.temporaryDirectory
                    .appendingPathComponent("HughesClipPrep-Captions-\(UUID().uuidString).ass")
                try writeASS(cues: cues, to: captionsURL)
                assURL = captionsURL
            }
        }

        defer {
            if let assURL {
                try? FileManager.default.removeItem(at: assURL)
            }
        }

        // Scale up to cover a 1080x1920 frame, then centre-crop. This handles
        // landscape, square, and already-vertical sources without special cases.
        var videoFilter = [
            "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos",
            "crop=1080:1920",
            "setsar=1",
            // DJI D-Log and HLG footage arrives 10-bit, which VideoToolbox will
            // not accept for H.264 without this conversion.
            "format=yuv420p"
        ]

        if let assURL {
            // Escape path characters FFmpeg's subtitles filter treats specially.
            let escaped = assURL.path
                .replacingOccurrences(of: "\\", with: "\\\\")
                .replacingOccurrences(of: ":", with: "\\:")
                .replacingOccurrences(of: "'", with: "\\'")
            videoFilter.append("ass='\(escaped)'")
        }

        let arguments = [
            "-hide_banner",
            "-loglevel",
            "warning",
            "-y",
            "-ss",
            String(format: "%.3f", candidate.startTime),
            "-i",
            videoURL.path,
            "-t",
            String(format: "%.3f", candidate.duration),
            "-vf",
            videoFilter.joined(separator: ","),
            // Shorts play loud; -14 LUFS matches what the platform targets.
            "-af",
            "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:v",
            "h264_videotoolbox",
            "-b:v",
            "8M",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            outputURL.path
        ]

        let exitCode = try await runProcess(
            executablePath: ffmpegPath,
            arguments: arguments,
            logURL: logURL
        )

        let logOutput = (try? String(contentsOf: logURL, encoding: .utf8)) ?? ""
        try? FileManager.default.removeItem(at: logURL)

        guard exitCode == 0,
              FileManager.default.fileExists(atPath: outputURL.path) else {
            // Only clean up a partial file this run created; a good clip from an
            // earlier run must survive a later failure.
            if !existedBeforeExport {
                try? FileManager.default.removeItem(at: outputURL)
            }

            throw ServiceError.processFailed(
                exitCode,
                logOutput.trimmingCharacters(in: .whitespacesAndNewlines)
            )
        }

        return outputURL
    }

    /// Big, high-contrast captions sized for phone screens with sound off.
    private static func writeASS(
        cues: [(start: TimeInterval, end: TimeInterval, text: String)],
        to url: URL
    ) throws {
        var lines = [
            "[Script Info]",
            "ScriptType: v4.00+",
            "PlayResX: 1080",
            "PlayResY: 1920",
            "WrapStyle: 0",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Shorts,Arial Black,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,0,2,60,60,220,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]

        for cue in cues {
            let text = cue.text
                .replacingOccurrences(of: "\\", with: "\\\\")
                .replacingOccurrences(of: "{", with: "\\{")
                .replacingOccurrences(of: "}", with: "\\}")

            lines.append(
                "Dialogue: 0,\(assTime(cue.start)),\(assTime(cue.end)),Shorts,,0,0,0,,\(text)"
            )
        }

        try lines.joined(separator: "\n").write(to: url, atomically: true, encoding: .utf8)
    }

    private static func assTime(_ seconds: TimeInterval) -> String {
        let totalCentiseconds = max(Int((seconds * 100).rounded()), 0)
        let hours = totalCentiseconds / 360_000
        let minutes = (totalCentiseconds % 360_000) / 6_000
        let secs = (totalCentiseconds % 6_000) / 100
        let cents = totalCentiseconds % 100

        return String(format: "%d:%02d:%02d.%02d", hours, minutes, secs, cents)
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
                continuation.resume(
                    throwing: ServiceError.processFailed(
                        -1,
                        "Could not create the Shorts export log file."
                    )
                )
                return
            }

            process.standardOutput = outputHandle
            process.standardError = outputHandle

            process.terminationHandler = { completedProcess in
                try? outputHandle.close()
                continuation.resume(returning: completedProcess.terminationStatus)
            }

            do {
                try process.run()
            } catch {
                try? outputHandle.close()
                continuation.resume(throwing: error)
            }
        }
    }
}
