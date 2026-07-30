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
        index: Int
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

        // Scale up to cover a 1080x1920 frame, then centre-crop. This handles
        // landscape, square, and already-vertical sources without special cases.
        let videoFilter = [
            "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos",
            "crop=1080:1920",
            "setsar=1",
            // DJI D-Log and HLG footage arrives 10-bit, which VideoToolbox will
            // not accept for H.264 without this conversion.
            "format=yuv420p"
        ].joined(separator: ",")

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
            videoFilter,
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
