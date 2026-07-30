import Foundation

struct ProductionPassSettings: Equatable {
    let isEnabled: Bool
    let longPauseSeconds: Double

    static let defaultLongPauseSeconds = 2.0

    static var enabledByDefault: ProductionPassSettings {
        ProductionPassSettings(
            isEnabled: true,
            longPauseSeconds: defaultLongPauseSeconds
        )
    }
}

enum ProductionPassService {
    enum ServiceError: LocalizedError {
        case ffmpegMissing
        case processFailed(Int32, String)

        var errorDescription: String? {
            switch self {
            case .ffmpegMissing:
                return "FFmpeg was not found. Install it with: brew install ffmpeg"
            case .processFailed(let code, let output):
                if output.isEmpty {
                    return "FFmpeg exited with code \(code)."
                }
                return "FFmpeg exited with code \(code): \(output)"
            }
        }
    }

    static var ffmpegPath: String? {
        let candidates = [
            "/opt/homebrew/bin/ffmpeg",
            "/usr/local/bin/ffmpeg"
        ]

        return candidates.first {
            FileManager.default.isExecutableFile(atPath: $0)
        }
    }

    static func apply(
        to videoURL: URL,
        settings: ProductionPassSettings
    ) async throws {
        guard settings.isEnabled else {
            return
        }

        guard let ffmpegPath else {
            throw ServiceError.ffmpegMissing
        }

        let temporaryURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("DJIClipCleaner-Production-\(UUID().uuidString).mp4")

        let logURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("DJIClipCleaner-FFmpeg-\(UUID().uuidString).log")

        FileManager.default.createFile(atPath: logURL.path, contents: nil)

        let pauseDuration = String(
            format: "%.2f",
            settings.longPauseSeconds
        )

        // Light denoise, broadcast loudness, then remove only long awkward pauses.
        let audioFilter = [
            "afftdn=nf=-20:nr=8",
            "highpass=f=90",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "silenceremove=stop_periods=-1:stop_duration=\(pauseDuration):stop_threshold=-40dB:start_periods=0"
        ].joined(separator: ",")

        let arguments = [
            "-hide_banner",
            "-loglevel",
            "warning",
            "-y",
            "-i",
            videoURL.path,
            "-af",
            audioFilter,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-b:a",
            "192k",
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
            throw ServiceError.processFailed(exitCode, logOutput.trimmingCharacters(in: .whitespacesAndNewlines))
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
                continuation.resume(throwing: ServiceError.processFailed(-1, "Could not create FFmpeg log file."))
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
