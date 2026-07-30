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

    /// What landed on disk after one Short export.
    struct ExportProduct: Sendable {
        let url: URL
        /// True when captions were burned into the MP4 pixels.
        let captionsBurnedIn: Bool
        /// Sidecar `.srt` when burn-in was impossible (minimal FFmpeg).
        let captionsSidecarURL: URL?
    }

    private enum CaptionBurnMode {
        case drawtext
        case ass
        case subtitles
        case sidecarOnly
    }

    static let outputFolderName = "Shorts"

    /// macOS font files that work with FFmpeg drawtext.
    private static let captionFontCandidates = [
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"
    ]

    private static var cachedFilterNames: Set<String>?

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
    ) async throws -> ExportProduct {
        guard let ffmpegPath = ProductionPassService.ffmpegPath else {
            throw ServiceError.ffmpegMissing
        }

        let folder = outputFolder(for: videoURL)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)

        let baseName = sanitizeFileName(
            videoURL.deletingPathExtension().lastPathComponent
        )
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

        var captionsBurnedIn = false
        var captionsSidecarURL: URL?
        var assURL: URL?

        defer {
            if let assURL {
                try? FileManager.default.removeItem(at: assURL)
            }
        }

        let storyCues = remappedCaptionCues(
            transcript: transcript,
            beats: candidate.beats
        )

        let mode = captionBurnMode(ffmpegPath: ffmpegPath)
        var burnFilters: [String] = []

        if !storyCues.isEmpty {
            switch mode {
            case .drawtext:
                burnFilters = drawTextCaptionFilters(cues: storyCues)
                captionsBurnedIn = true

            case .ass, .subtitles:
                let safeName = "hcp\(UUID().uuidString.replacingOccurrences(of: "-", with: "")).ass"
                let captionsURL = FileManager.default.temporaryDirectory
                    .appendingPathComponent(safeName)
                try writeASS(cues: storyCues, to: captionsURL)
                assURL = captionsURL
                let escaped = escapeFilterPath(captionsURL.path)
                burnFilters = [
                    mode == .ass
                        ? "ass=filename=\(escaped)"
                        : "subtitles=filename=\(escaped)"
                ]
                captionsBurnedIn = true

            case .sidecarOnly:
                let srtURL = folder.appendingPathComponent(
                    "\(baseName)_short_\(position)_\(sourceSecond)s.srt"
                )
                try writeSRT(cues: storyCues, to: srtURL)
                captionsSidecarURL = srtURL
            }
        }

        let arguments: [String]
        if candidate.beats.count <= 1 {
            let beat = candidate.beats.first
            let start = beat?.startTime ?? candidate.startTime
            let duration = beat?.duration ?? candidate.duration

            var videoFilter = [
                "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos",
                "crop=1080:1920",
                "setsar=1",
                "format=yuv420p"
            ]
            videoFilter.append(contentsOf: burnFilters)

            arguments = [
                "-hide_banner", "-loglevel", "warning", "-y",
                "-ss", String(format: "%.3f", start),
                "-i", videoURL.path,
                "-t", String(format: "%.3f", duration),
                "-vf", videoFilter.joined(separator: ","),
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                "-c:v", "h264_videotoolbox", "-b:v", "8M", "-r", "30",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                outputURL.path
            ]
        } else {
            // Splice hook / payoff / button from different source times into one
            // vertical Short. Captions (if any) burn after the concat.
            let complex = spliceFilterComplex(
                beats: candidate.beats,
                burnFilters: burnFilters
            )

            arguments = [
                "-hide_banner", "-loglevel", "warning", "-y",
                "-i", videoURL.path,
                "-filter_complex", complex.filter,
                "-map", complex.videoMap,
                "-map", complex.audioMap,
                "-c:v", "h264_videotoolbox", "-b:v", "8M", "-r", "30",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                outputURL.path
            ]
        }

        let exitCode = try await runProcess(
            executablePath: ffmpegPath,
            arguments: arguments,
            logURL: logURL
        )

        let logOutput = (try? String(contentsOf: logURL, encoding: .utf8)) ?? ""
        try? FileManager.default.removeItem(at: logURL)

        guard exitCode == 0,
              FileManager.default.fileExists(atPath: outputURL.path) else {
            if !existedBeforeExport {
                try? FileManager.default.removeItem(at: outputURL)
            }

            throw ServiceError.processFailed(
                exitCode,
                logOutput.trimmingCharacters(in: .whitespacesAndNewlines)
            )
        }

        return ExportProduct(
            url: outputURL,
            captionsBurnedIn: captionsBurnedIn,
            captionsSidecarURL: captionsSidecarURL
        )
    }

    /// Rebuild caption timings onto the spliced timeline (0…totalDuration).
    private static func remappedCaptionCues(
        transcript: Transcript?,
        beats: [ShortBeat]
    ) -> [(start: TimeInterval, end: TimeInterval, text: String)] {
        guard let transcript, !beats.isEmpty else { return [] }

        var offset: TimeInterval = 0
        var cues: [(start: TimeInterval, end: TimeInterval, text: String)] = []

        for beat in beats {
            let local = transcript.captionCues(
                overlapping: beat.startTime,
                duration: beat.duration
            )

            for cue in local {
                cues.append(
                    (
                        start: offset + cue.start,
                        end: offset + cue.end,
                        text: cue.text
                    )
                )
            }

            offset += beat.duration
        }

        return cues
    }

    private static func spliceFilterComplex(
        beats: [ShortBeat],
        burnFilters: [String]
    ) -> (filter: String, videoMap: String, audioMap: String) {
        var parts: [String] = []
        var concatInputs = ""

        for (index, beat) in beats.enumerated() {
            let start = String(format: "%.3f", beat.startTime)
            let duration = String(format: "%.3f", beat.duration)
            parts.append(
                "[0:v]trim=start=\(start):duration=\(duration),setpts=PTS-STARTPTS,"
                    + "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
                    + "crop=1080:1920,setsar=1,format=yuv420p[v\(index)]"
            )
            parts.append(
                "[0:a]atrim=start=\(start):duration=\(duration),asetpts=PTS-STARTPTS[a\(index)]"
            )
            concatInputs += "[v\(index)][a\(index)]"
        }

        let count = beats.count
        let videoOut = burnFilters.isEmpty ? "[vout]" : "[vcat]"
        parts.append("\(concatInputs)concat=n=\(count):v=1:a=1\(videoOut)[acat]")
        parts.append("[acat]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

        if !burnFilters.isEmpty {
            // Burn after the story is assembled so timings match the Short.
            parts.append("[vcat]\(burnFilters.joined(separator: ","))[vout]")
        }

        return (
            filter: parts.joined(separator: ";"),
            videoMap: "[vout]",
            audioMap: "[aout]"
        )
    }

    // MARK: - Caption strategy

    /// Prefer burn-in filters when the installed FFmpeg has them; otherwise
    /// fall back to a sidecar so export never hard-fails on missing filters.
    private static func captionBurnMode(ffmpegPath: String) -> CaptionBurnMode {
        let filters = probeFilters(ffmpegPath: ffmpegPath)

        if filters.contains("drawtext") {
            return .drawtext
        }
        if filters.contains("ass") {
            return .ass
        }
        if filters.contains("subtitles") {
            return .subtitles
        }
        return .sidecarOnly
    }

    private static func probeFilters(ffmpegPath: String) -> Set<String> {
        if let cachedFilterNames {
            return cachedFilterNames
        }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: ffmpegPath)
        process.arguments = ["-hide_banner", "-filters"]

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        do {
            try process.run()
            process.waitUntilExit()
        } catch {
            cachedFilterNames = []
            return []
        }

        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        let text = String(data: data, encoding: .utf8) ?? ""

        // Lines look like: " ... drawtext           V->V       Draw text on top of video"
        var names = Set<String>()
        for line in text.split(whereSeparator: \.isNewline) {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            guard trimmed.count > 4 else { continue }

            let parts = trimmed.split(whereSeparator: \.isWhitespace)
            guard parts.count >= 2 else { continue }

            // First token is flags (T.C etc.); second is the filter name.
            let candidate = String(parts[1])
            if candidate.allSatisfy({ $0.isLetter || $0.isNumber || $0 == "_" }) {
                names.insert(candidate)
            }
        }

        cachedFilterNames = names
        return names
    }

    // MARK: - drawtext burn-in

    /// One drawtext filter per cue. Cue times are already relative to the Short
    /// window (0…duration), matching `-ss` before `-i`.
    private static func drawTextCaptionFilters(
        cues: [(start: TimeInterval, end: TimeInterval, text: String)]
    ) -> [String] {
        let fontFile = captionFontCandidates.first {
            FileManager.default.fileExists(atPath: $0)
        }

        // Cap cue count so a long chatty Short cannot explode the filtergraph.
        return cues.prefix(48).compactMap { cue in
            let text = escapeDrawText(cue.text)
            guard !text.isEmpty else { return nil }

            let start = max(cue.start, 0)
            let end = max(cue.end, start + 0.15)
            let startText = String(format: "%.2f", start)
            let endText = String(format: "%.2f", end)

            var options = [
                "text='\(text)'",
                "fontsize=68",
                "fontcolor=white",
                "borderw=5",
                "bordercolor=black",
                "x=(w-text_w)/2",
                "y=h-240",
                // Commas inside enable= must be filtergraph-escaped.
                "enable='between(t\\,\(startText)\\,\(endText))'"
            ]

            if let fontFile {
                options.insert(
                    "fontfile=\(escapeFilterPath(fontFile))",
                    at: 0
                )
            }

            return "drawtext=\(options.joined(separator: ":"))"
        }
    }

    // MARK: - ASS / SRT writers

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

    private static func writeSRT(
        cues: [(start: TimeInterval, end: TimeInterval, text: String)],
        to url: URL
    ) throws {
        var lines: [String] = []

        for (index, cue) in cues.enumerated() {
            lines.append("\(index + 1)")
            lines.append("\(srtTime(cue.start)) --> \(srtTime(cue.end))")
            lines.append(cue.text)
            lines.append("")
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

    private static func srtTime(_ seconds: TimeInterval) -> String {
        let totalMilliseconds = max(Int((seconds * 1_000).rounded()), 0)
        let hours = totalMilliseconds / 3_600_000
        let minutes = (totalMilliseconds % 3_600_000) / 60_000
        let secs = (totalMilliseconds % 60_000) / 1_000
        let millis = totalMilliseconds % 1_000

        return String(format: "%02d:%02d:%02d,%03d", hours, minutes, secs, millis)
    }

    // MARK: - Escaping / naming

    /// Escape a caption string for drawtext's `text='…'` form.
    private static func escapeDrawText(_ text: String) -> String {
        text
            .replacingOccurrences(of: "\\", with: "\\\\")
            // Straight apostrophe breaks the quoted option; use a typographic one.
            .replacingOccurrences(of: "'", with: "\u{2019}")
            .replacingOccurrences(of: ":", with: "\\:")
            .replacingOccurrences(of: "%", with: "%%")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// Characters that break FFmpeg filter option values when left bare.
    private static func escapeFilterPath(_ path: String) -> String {
        path
            .replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: ":", with: "\\:")
            .replacingOccurrences(of: "'", with: "\\'")
            .replacingOccurrences(of: "[", with: "\\[")
            .replacingOccurrences(of: "]", with: "\\]")
            .replacingOccurrences(of: ",", with: "\\,")
            .replacingOccurrences(of: ";", with: "\\;")
            .replacingOccurrences(of: " ", with: "\\ ")
    }

    /// Filmora / Finder names often include spaces and "(copy)" — fine for
    /// Process argv, but messy in Finder and sometimes trip older tooling.
    private static func sanitizeFileName(_ name: String) -> String {
        let cleaned = name
            .replacingOccurrences(of: "(copy)", with: "", options: .caseInsensitive)
            .replacingOccurrences(of: " ", with: "_")
            .replacingOccurrences(of: "(", with: "")
            .replacingOccurrences(of: ")", with: "")
            .replacingOccurrences(of: "/", with: "-")
            .replacingOccurrences(of: ":", with: "-")

        let collapsed = cleaned.replacingOccurrences(
            of: "_+",
            with: "_",
            options: .regularExpression
        )

        return collapsed.trimmingCharacters(in: CharacterSet(charactersIn: "._-"))
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
