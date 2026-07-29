import Foundation

enum StabilizationService {
    enum ServiceError: LocalizedError {
        case ffmpegMissing
        case processFailed(Int32, String)

        var errorDescription: String? {
            switch self {
            case .ffmpegMissing:
                return "FFmpeg was not found. Install it with: brew install ffmpeg"
            case .processFailed(let code, let output):
                if output.isEmpty {
                    return "Stabilization failed with exit code \(code)."
                }
                return "Stabilization failed with exit code \(code): \(output)"
            }
        }
    }

    static func apply(to videoURL: URL) async throws {
        guard let ffmpegPath = ProductionPassService.ffmpegPath else {
            throw ServiceError.ffmpegMissing
        }

        let temporaryURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("HughesClipPrep-Stabilize-\(UUID().uuidString).mp4")

        let logURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("HughesClipPrep-Stabilize-\(UUID().uuidString).log")

        FileManager.default.createFile(atPath: logURL.path, contents: nil)

        let arguments = [
            "-hide_banner",
            "-loglevel",
            "warning",
            "-y",
            "-i",
            videoURL.path,
            "-vf",
            "deshake=rx=16:ry=16:edge=blank",
            "-c:v",
            "h264_videotoolbox",
            "-b:v",
            "10M",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            temporaryURL.path
        ]

        let exitCode = try await runProcess(
            executablePath: ffmpegPath,
            arguments: arguments,
            logURL: logURL
        )

        let logOutput = (try? String(contentsOf: logURL, encoding: .utf8)) ?? ""
        try? FileManager.default.removeItem(at: logURL)

        guard exitCode == 0,
              FileManager.default.fileExists(atPath: temporaryURL.path) else {
            try? FileManager.default.removeItem(at: temporaryURL)
            throw ServiceError.processFailed(
                exitCode,
                logOutput.trimmingCharacters(in: .whitespacesAndNewlines)
            )
        }

        _ = try FileManager.default.replaceItemAt(
            videoURL,
            withItemAt: temporaryURL
        )
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
                        "Could not create stabilization log file."
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
