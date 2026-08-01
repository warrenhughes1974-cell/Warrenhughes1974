import AVFoundation
import Foundation

#if canImport(AppKit)
import AppKit
#endif

struct OpenAIUploadCopy: Sendable {
    let title: String
    let description: String
    let tags: [String]
    let hashtags: [String]
    let thumbnailText: String
}

struct OpenAIVisionThumbnailPick: Sendable {
    /// Index into the candidate list that was sent to Vision (0-based).
    let localIndex: Int
    let overlayText: String
    let reason: String
}

struct OpenAIVisionThumbnailPlan: Sendable {
    let picks: [OpenAIVisionThumbnailPick]
}

struct OpenAIClipAssist: Sendable {
    let label: ClipRecommendation
    let reason: String
}

struct OpenAICutHintRange: Sendable {
    enum Action: String, Sendable {
        case keep = "KEEP"
        case cut = "CUT"
    }

    let action: Action
    let startSeconds: TimeInterval
    let endSeconds: TimeInterval
    let reason: String
}

struct OpenAICutHints: Sendable {
    let summary: String
    let ranges: [OpenAICutHintRange]

    /// Compact table/CSV string, e.g. `KEEP 0:08–0:41 talking · CUT 0:00–0:07 dead air`.
    var displayString: String {
        let parts = ranges.map { range in

            let start = TranscriptChapter.timecode(range.startSeconds)
            let end = TranscriptChapter.timecode(range.endSeconds)
            let reason = range.reason.trimmingCharacters(in: .whitespacesAndNewlines)
            if reason.isEmpty {
                return "\(range.action.rawValue) \(start)–\(end)"
            }
            return "\(range.action.rawValue) \(start)–\(end) \(reason)"
        }
        let joined = parts.joined(separator: " · ")
        let head = summary.trimmingCharacters(in: .whitespacesAndNewlines)
        if head.isEmpty { return joined }
        if joined.isEmpty { return head }
        return "\(head) | \(joined)"
    }
}

/// Cloud OpenAI helpers for Whisper transcription and GPT story/copy.
/// Requires a user-provided API key stored in Keychain.
enum OpenAIClient {
    enum ServiceError: LocalizedError {
        case missingAPIKey
        case ffmpegMissing
        case audioExtractFailed
        case httpStatus(Int, String)
        case emptyResult
        case decodingFailed
        case invalidResponse

        var errorDescription: String? {
            switch self {
            case .missingAPIKey:
                return "Add your OpenAI API key in Settings before using cloud AI."
            case .ffmpegMissing:
                return "FFmpeg was not found. Install it with: brew install ffmpeg"
            case .audioExtractFailed:
                return "Could not extract audio for OpenAI Whisper."
            case .httpStatus(let code, let body):
                return "OpenAI request failed (\(code)): \(body)"
            case .emptyResult:
                return "OpenAI returned an empty result."
            case .decodingFailed:
                return "Could not read the OpenAI response."
            case .invalidResponse:
                return "OpenAI returned an unexpected response."
            }
        }
    }

    private static let transcriptionURL = URL(string: "https://api.openai.com/v1/audio/transcriptions")!
    private static let chatURL = URL(string: "https://api.openai.com/v1/chat/completions")!
    private static let maxUploadBytes = 24 * 1_024 * 1_024
    private static let chunkSeconds: TimeInterval = 600

    // MARK: - Whisper

    static func transcribeWithWhisper(
        videoURL: URL,
        apiKey: String
    ) async throws -> Transcript {
        guard !apiKey.isEmpty else { throw ServiceError.missingAPIKey }

        let audioURL = try await extractCompressedAudio(from: videoURL)
        defer { try? FileManager.default.removeItem(at: audioURL) }

        let fileSize = (try? audioURL.resourceValues(forKeys: [.fileSizeKey]).fileSize) ?? 0
        if fileSize > 0, fileSize <= maxUploadBytes {
            return try await transcribeAudioFile(
                audioURL,
                apiKey: apiKey,
                timeOffset: 0
            )
        }

        // Long / large files: chunk by time so each upload stays under the limit.
        let assetDuration = try await audioDuration(of: audioURL)
        guard assetDuration > 0.5 else { throw ServiceError.emptyResult }

        var segments: [TranscriptSegment] = []
        var cursor: TimeInterval = 0
        while cursor < assetDuration {
            let length = min(chunkSeconds, assetDuration - cursor)
            let chunkURL = try await exportAudioChunk(
                from: audioURL,
                start: cursor,
                duration: length
            )
            defer { try? FileManager.default.removeItem(at: chunkURL) }

            let chunk = try await transcribeAudioFile(
                chunkURL,
                apiKey: apiKey,
                timeOffset: cursor
            )
            segments.append(contentsOf: chunk.segments)
            cursor += length
        }

        guard !segments.isEmpty else { throw ServiceError.emptyResult }
        let fullText = segments.map(\.text).joined(separator: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        return Transcript(
            fullText: fullText,
            segments: segments,
            languageCode: "en",
            usedOnDevice: false
        )
    }

    // MARK: - Story analysis

    static func analyzeStory(
        transcript: Transcript,
        existingHook: String,
        brand: BrandSettingsValues,
        model: String,
        apiKey: String
    ) async throws -> StoryAnalysis {
        let prompt = """
        Analyze this video transcript and return ONLY JSON with these keys:
        domain (one of: travelDelay, retailHunt, cooking, motorsport, adventure, themePark, cruise, family, general),
        subject, goal, obstacle, origin, problemLocation, destination, outcome, summary,
        confidence (0-100), visualTargets (array of strings), titleIdeas (array),
        thumbnailTextIdeas (array of 2-4 word phrases), tags (array), hashtags (array max 3),
        chapters (array of {startTimeSeconds:number, title:string}).

        Rules:
        - Empty string when unknown. Never invent travelers, pets on the trip, or places.
        - A person is a traveler only with explicit on-trip cues (coworker joining, traveling with, left from).
        - Mentions as at home / not coming / seeing later / own bed are NOT travelers.
        - Channel context is spelling/identity only, never plot evidence.
        - Titles and summary must be grammatical complete phrases. Never output fragments like "and 's ...".
        - Prefer first person ("I") when the speaker is the traveler.
        - Hashtags must be earned by spoken topics.

        Existing hook (may be stale): \(existingHook)

        Channel context:
        \(brand.channelContext)

        Transcript:
        \(String(transcript.fullText.prefix(12_000)))
        """

        let content = try await chatCompletion(
            model: model,
            apiKey: apiKey,
            system: "You are a factual YouTube story analyst. Return compact JSON only.",
            user: prompt,
            jsonMode: true
        )

        return try decodeStoryAnalysis(from: content)
    }

    // MARK: - Upload copy

    static func generateUploadCopy(
        analysis: StoryAnalysis,
        title: String,
        brand: BrandSettingsValues,
        transcript: Transcript?,
        model: String,
        apiKey: String
    ) async throws -> OpenAIUploadCopy {
        let pack = YouTubeMetadataService.chatGPTPack(
            analysis: analysis,
            title: title,
            brand: brand,
            transcript: transcript
        )

        let prompt = """
        \(pack)

        Return ONLY JSON with keys:
        title (string),
        description (string, ready to paste into YouTube),
        tags (array of searchable phrases),
        hashtags (array max 3),
        thumbnailText (2-4 words, uppercase OK).
        """

        let content = try await chatCompletion(
            model: model,
            apiKey: apiKey,
            system: "You write publish-ready YouTube metadata. JSON only. Never invent cast or places.",
            user: prompt,
            jsonMode: true
        )

        return try decodeUploadCopy(from: content)
    }

    // MARK: - Smart Analysis AI Assist

    /// Second-opinion triage for one clip using local metrics only (no invent).
    /// Caller merges with local rules via `RecommendationEngine.mergeAIAssist`.
    static func assistClipRecommendation(
        fileName: String,
        local: ClipRecommendation,
        localNotes: String,
        talkingPercent: Double,
        motionPercent: Double,
        durationSeconds: Double,
        jerkSummary: String,
        transcriptSnippet: String?,
        model: String,
        apiKey: String
    ) async throws -> OpenAIClipAssist {
        guard !apiKey.isEmpty else { throw ServiceError.missingAPIKey }

        let snippet = (transcriptSnippet ?? "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        let snippetBlock = snippet.isEmpty
            ? "(no transcript snippet)"
            : String(snippet.prefix(700))

        let prompt = """
        You triage one DJI/travel vlog clip for KEEP / B-ROLL / REVIEW / DISCARD.
        Use ONLY the numbers and notes below. Never invent people, places, or plot.

        File: \(fileName)
        Duration seconds: \(String(format: "%.1f", durationSeconds))
        Talking percent (loudness proxy): \(String(format: "%.1f", talkingPercent))
        Motion percent: \(String(format: "%.1f", motionPercent))
        Sudden movement: \(jerkSummary.isEmpty ? "none noted" : jerkSummary)
        Local label: \(local.rawValue)
        Local notes: \(localNotes)
        Transcript snippet: \(snippetBlock)

        Prefer demoting obvious junk (camera on table, dead hallway, almost no useful content).
        Do not upgrade weak clips to KEEP without strong talking evidence in the numbers.
        B-ROLL = useful silent cutaway/scenic motion. DISCARD = not worth editing.

        Return ONLY JSON:
        { "label": "KEEP"|"B-ROLL"|"REVIEW"|"DISCARD", "reason": "short factual reason" }
        """

        let raw = try await chatCompletion(
            model: model,
            apiKey: apiKey,
            system: "You are a clip triage assistant. JSON only. Never invent facts.",
            user: prompt,
            jsonMode: true
        )
        return try decodeClipAssist(from: raw)
    }

    /// Suggest KEEP/CUT time ranges from a timed transcript. Hints only — no export edits.
    static func suggestCutHints(
        fileName: String,
        recommendation: ClipRecommendation,
        durationSeconds: Double,
        transcript: Transcript,
        model: String,
        apiKey: String
    ) async throws -> OpenAICutHints {
        guard !apiKey.isEmpty else { throw ServiceError.missingAPIKey }
        guard durationSeconds > 1 else { throw ServiceError.emptyResult }

        let timed = timedTranscriptBlock(from: transcript, maxChars: 2_800)
        guard !timed.isEmpty else { throw ServiceError.emptyResult }

        let prompt = """
        You are an editor assistant for a travel/vlog channel.
        Suggest KEEP and CUT time ranges inside ONE clip so the human can trim faster in Filmora.
        Do NOT invent people, places, or plot. Use ONLY the timed transcript.

        File: \(fileName)
        Clip duration seconds: \(String(format: "%.1f", durationSeconds))
        Local recommendation: \(recommendation.rawValue)

        Timed transcript:
        \(timed)

        Rules:
        - Prefer 1–2 KEEP ranges for usable talking or strong silent B-roll.
        - CUT dead air, false starts, "wait hold on", packing/table noise, walking with no story.
        - Times must be within 0 … \(String(format: "%.1f", durationSeconds)).
        - startSeconds < endSeconds.
        - Max 6 ranges total.
        - Reasons short and factual.

        Return ONLY JSON:
        {
          "summary": "one short line",
          "hints": [
            { "action": "KEEP"|"CUT", "startSeconds": 0, "endSeconds": 10, "reason": "short" }
          ]
        }
        """

        let raw = try await chatCompletion(
            model: model,
            apiKey: apiKey,
            system: "You suggest edit cut hints from transcripts. JSON only. Never invent facts.",
            user: prompt,
            jsonMode: true
        )
        return try decodeCutHints(from: raw, durationSeconds: durationSeconds)
    }

    // MARK: - Shorts refine

    /// Reorders local Short candidates and rewrites clickable titles. Never changes cut times.
    static func refineShortCandidates(
        candidates: [ShortCandidate],
        transcript: Transcript,
        longFormTitle: String,
        themeBrief: String = "",
        brand: BrandSettingsValues,
        preset: BrandPreset,
        model: String,
        apiKey: String
    ) async throws -> [ShortCandidate] {
        guard !apiKey.isEmpty else { throw ServiceError.missingAPIKey }
        guard !candidates.isEmpty else { return candidates }

        let prompt = ShortsCloudRefine.prompt(
            candidates: candidates,
            transcript: transcript,
            longFormTitle: longFormTitle,
            themeBrief: themeBrief,
            brand: brand,
            preset: preset
        )

        let raw = try await chatCompletion(
            model: model,
            apiKey: apiKey,
            system: "You rank YouTube Shorts moments and write titles. JSON only. Never invent cast or places. Never change cut times.",
            user: prompt,
            jsonMode: true
        )
        return try ShortsCloudRefine.apply(json: raw, to: candidates)
    }

    // MARK: - Vision thumbnails

    /// Reranks local thumbnail candidates and suggests 2–4 word overlays that
    /// match what is actually visible in each frame.
    static func rankThumbnailFrames(
        jpegImages: [Data],
        storySummary: String,
        domain: String,
        currentOverlay: String,
        model: String,
        apiKey: String
    ) async throws -> OpenAIVisionThumbnailPlan {
        guard !apiKey.isEmpty else { throw ServiceError.missingAPIKey }
        guard !jpegImages.isEmpty else { throw ServiceError.emptyResult }

        var content: [[String: Any]] = [
            [
                "type": "text",
                "text": """
                You are a YouTube thumbnail director for a real travel/vlog channel.
                Rank these \(jpegImages.count) frames from best to worst click-through.
                Prefer emotion, clear subject, strong composition, and story fit.
                Avoid blurry, dull, empty, or face-filling frames.

                Story type: \(domain)
                Story summary: \(storySummary)
                Current overlay idea: \(currentOverlay)

                Return ONLY JSON:
                {
                  "picks": [
                    {
                      "index": 0,
                      "overlayText": "2 TO 4 WORDS",
                      "reason": "short reason"
                    }
                  ]
                }
                - index is 0-based into the images below (image 1 = index 0).
                - Include every image exactly once, best first.
                - overlayText must match what is visible + the story. Uppercase OK.
                - Never invent people who are not on this trip.
                """
            ]
        ]

        for (offset, jpeg) in jpegImages.enumerated() {
            let base64 = jpeg.base64EncodedString()
            content.append([
                "type": "text",
                "text": "Image \(offset + 1) (index \(offset)):"
            ])
            content.append([
                "type": "image_url",
                "image_url": [
                    "url": "data:image/jpeg;base64,\(base64)",
                    "detail": "low"
                ]
            ])
        }

        // Vision needs a model that accepts images; fall back to gpt-4o-mini.
        let visionModel = model.lowercased().contains("gpt-4o") ? model : "gpt-4o-mini"
        let raw = try await chatCompletion(
            model: visionModel,
            apiKey: apiKey,
            system: "You pick clickable YouTube thumbnails. JSON only.",
            userContent: content,
            jsonMode: true
        )
        return try decodeVisionPlan(from: raw, imageCount: jpegImages.count)
    }

    // MARK: - HTTP

    private static func chatCompletion(
        model: String,
        apiKey: String,
        system: String,
        user: String,
        jsonMode: Bool
    ) async throws -> String {
        try await chatCompletion(
            model: model,
            apiKey: apiKey,
            system: system,
            userContent: [["type": "text", "text": user]],
            jsonMode: jsonMode
        )
    }

    private static func chatCompletion(
        model: String,
        apiKey: String,
        system: String,
        userContent: [[String: Any]],
        jsonMode: Bool
    ) async throws -> String {
        var request = URLRequest(url: chatURL)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 180

        var body: [String: Any] = [
            "model": model,
            "temperature": 0.3,
            "messages": [
                ["role": "system", "content": system],
                ["role": "user", "content": userContent]
            ]
        ]
        if jsonMode {
            body["response_format"] = ["type": "json_object"]
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)
        try throwIfNeeded(data: data, response: response)

        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let choices = root["choices"] as? [[String: Any]],
              let message = choices.first?["message"] as? [String: Any],
              let content = message["content"] as? String,
              !content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw ServiceError.invalidResponse
        }
        return content
    }

    private static func transcribeAudioFile(
        _ audioURL: URL,
        apiKey: String,
        timeOffset: TimeInterval
    ) async throws -> Transcript {
        let boundary = "Boundary-\(UUID().uuidString)"
        var request = URLRequest(url: transcriptionURL)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue(
            "multipart/form-data; boundary=\(boundary)",
            forHTTPHeaderField: "Content-Type"
        )
        request.timeoutInterval = 300

        let filename = audioURL.lastPathComponent
        let fileData = try Data(contentsOf: audioURL)
        var body = Data()
        func append(_ string: String) {
            body.append(Data(string.utf8))
        }

        append("--\(boundary)\r\n")
        append("Content-Disposition: form-data; name=\"model\"\r\n\r\n")
        append("whisper-1\r\n")

        append("--\(boundary)\r\n")
        append("Content-Disposition: form-data; name=\"response_format\"\r\n\r\n")
        append("verbose_json\r\n")

        append("--\(boundary)\r\n")
        append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n")
        append("Content-Type: application/octet-stream\r\n\r\n")
        body.append(fileData)
        append("\r\n")
        append("--\(boundary)--\r\n")
        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)
        try throwIfNeeded(data: data, response: response)

        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw ServiceError.decodingFailed
        }

        let fullText = (root["text"] as? String ?? "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        let rawSegments = root["segments"] as? [[String: Any]] ?? []

        var segments: [TranscriptSegment] = []
        for item in rawSegments {
            let text = (item["text"] as? String ?? "")
                .trimmingCharacters(in: .whitespacesAndNewlines)
            guard !text.isEmpty else { continue }
            let start = (item["start"] as? Double) ?? 0
            let end = (item["end"] as? Double) ?? (start + 0.5)
            segments.append(
                TranscriptSegment(
                    text: text,
                    startTime: timeOffset + max(start, 0),
                    duration: max(end - start, 0.05)
                )
            )
        }

        if segments.isEmpty, !fullText.isEmpty {
            segments = [
                TranscriptSegment(text: fullText, startTime: timeOffset, duration: 1)
            ]
        }

        guard !fullText.isEmpty || !segments.isEmpty else {
            throw ServiceError.emptyResult
        }

        return Transcript(
            fullText: fullText.isEmpty
                ? segments.map(\.text).joined(separator: " ")
                : fullText,
            segments: segments,
            languageCode: (root["language"] as? String) ?? "en",
            usedOnDevice: false
        )
    }

    private static func throwIfNeeded(data: Data, response: URLResponse) throws {
        let code = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200...299).contains(code) else {
            let body = String(data: data, encoding: .utf8)?
                .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            let clipped = body.count > 280 ? String(body.prefix(280)) + "…" : body
            throw ServiceError.httpStatus(code, clipped.isEmpty ? "No details" : clipped)
        }
    }

    // MARK: - Decoding

    static func decodeStoryAnalysis(from json: String) throws -> StoryAnalysis {
        guard let data = json.data(using: .utf8),
              let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw ServiceError.decodingFailed
        }

        let domainRaw = (root["domain"] as? String) ?? "general"
        let domain = StoryDomain(rawValue: domainRaw) ?? .general
        let chaptersJSON = root["chapters"] as? [[String: Any]] ?? []
        let chapters: [StoryChapterCandidate] = chaptersJSON.compactMap { item in
            let title = (item["title"] as? String ?? "")
                .trimmingCharacters(in: .whitespacesAndNewlines)
            guard !title.isEmpty else { return nil }
            let start = (item["startTimeSeconds"] as? Double)
                ?? (item["startTime"] as? Double)
                ?? 0
            return StoryChapterCandidate(startTime: max(start, 0), title: title)
        }

        return StoryAnalysis(
            domain: domain,
            subject: stringValue(root["subject"]),
            goal: stringValue(root["goal"]),
            obstacle: stringValue(root["obstacle"]),
            origin: stringValue(root["origin"]),
            problemLocation: stringValue(root["problemLocation"]),
            destination: stringValue(root["destination"]),
            outcome: stringValue(root["outcome"]),
            summary: stringValue(root["summary"]),
            evidence: stringArray(root["evidence"]),
            confidence: min(max(intValue(root["confidence"]) ?? 70, 0), 100),
            visualTargets: stringArray(root["visualTargets"]),
            titleIdeas: stringArray(root["titleIdeas"]),
            thumbnailTextIdeas: stringArray(root["thumbnailTextIdeas"]),
            chapters: chapters,
            tags: stringArray(root["tags"]),
            hashtags: Array(stringArray(root["hashtags"]).prefix(3).map { tag in
                tag.hasPrefix("#") ? tag : "#\(tag.replacingOccurrences(of: "#", with: ""))"
            }),
            source: .openAI
        )
    }

    static func decodeUploadCopy(from json: String) throws -> OpenAIUploadCopy {
        guard let data = json.data(using: .utf8),
              let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw ServiceError.decodingFailed
        }

        let title = stringValue(root["title"])
        let description = stringValue(root["description"])
        guard !description.isEmpty else { throw ServiceError.emptyResult }

        return OpenAIUploadCopy(
            title: title,
            description: description,
            tags: stringArray(root["tags"]),
            hashtags: stringArray(root["hashtags"]),
            thumbnailText: stringValue(root["thumbnailText"])
        )
    }

    static func decodeClipAssist(from json: String) throws -> OpenAIClipAssist {
        guard let data = json.data(using: .utf8),
              let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw ServiceError.decodingFailed
        }

        let rawLabel = stringValue(root["label"]).uppercased()
        let label: ClipRecommendation
        switch rawLabel {
        case "KEEP":
            label = .keep
        case "B-ROLL", "BROLL", "B ROLL":
            label = .bRoll
        case "REVIEW":
            label = .review
        case "DISCARD":
            label = .discard
        default:
            throw ServiceError.decodingFailed
        }

        return OpenAIClipAssist(
            label: label,
            reason: stringValue(root["reason"])
        )
    }

    static func decodeCutHints(
        from json: String,
        durationSeconds: Double
    ) throws -> OpenAICutHints {
        guard let data = json.data(using: .utf8),
              let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw ServiceError.decodingFailed
        }

        let hintsJSON = (root["hints"] as? [[String: Any]])
            ?? (root["ranges"] as? [[String: Any]])
            ?? []

        var ranges: [OpenAICutHintRange] = []
        for item in hintsJSON.prefix(6) {
            let actionRaw = stringValue(item["action"]).uppercased()
            let action: OpenAICutHintRange.Action?
            switch actionRaw {
            case "KEEP", "USE", "KEEP_RANGE":
                action = .keep
            case "CUT", "TRIM", "REMOVE", "CUT_OUT":
                action = .cut
            default:
                action = nil
            }
            guard let action else { continue }

            let start = doubleValue(item["startSeconds"]) ?? doubleValue(item["start"]) ?? -1
            let end = doubleValue(item["endSeconds"]) ?? doubleValue(item["end"]) ?? -1
            guard start >= 0, end > start else { continue }

            let clampedStart = min(max(start, 0), durationSeconds)
            let clampedEnd = min(max(end, clampedStart + 0.2), durationSeconds)
            guard clampedEnd > clampedStart else { continue }

            ranges.append(
                OpenAICutHintRange(
                    action: action,
                    startSeconds: clampedStart,
                    endSeconds: clampedEnd,
                    reason: stringValue(item["reason"])
                )
            )
        }

        let summary = stringValue(root["summary"])
        guard !ranges.isEmpty || !summary.isEmpty else {
            throw ServiceError.emptyResult
        }

        return OpenAICutHints(summary: summary, ranges: ranges)
    }

    static func timedTranscriptBlock(
        from transcript: Transcript,
        maxChars: Int
    ) -> String {
        var lines: [String] = []
        var used = 0
        for segment in transcript.segments {
            let text = segment.text.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !text.isEmpty else { continue }
            let line = "[\(TranscriptChapter.timecode(segment.startTime))-\(TranscriptChapter.timecode(segment.endTime))] \(text)"
            if used + line.count + 1 > maxChars { break }
            lines.append(line)
            used += line.count + 1
        }
        if lines.isEmpty {
            let full = transcript.fullText.trimmingCharacters(in: .whitespacesAndNewlines)
            return String(full.prefix(maxChars))
        }
        return lines.joined(separator: "\n")
    }

    static func doubleValue(_ any: Any?) -> Double? {
        if let value = any as? Double { return value }
        if let value = any as? Int { return Double(value) }
        if let value = any as? String { return Double(value) }
        return nil
    }

    static func decodeVisionPlan(
        from json: String,
        imageCount: Int
    ) throws -> OpenAIVisionThumbnailPlan {
        guard let data = json.data(using: .utf8),
              let root = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let picksJSON = root["picks"] as? [[String: Any]] else {
            throw ServiceError.decodingFailed
        }

        var seen = Set<Int>()
        var picks: [OpenAIVisionThumbnailPick] = []
        for item in picksJSON {
            let index = intValue(item["index"]) ?? -1
            guard index >= 0, index < imageCount, !seen.contains(index) else { continue }
            seen.insert(index)
            let overlay = stringValue(item["overlayText"]).uppercased()
            let words = overlay.split(separator: " ").count
            let safeOverlay = (2...4).contains(words) ? overlay : stringValue(item["overlayText"])
            picks.append(
                OpenAIVisionThumbnailPick(
                    localIndex: index,
                    overlayText: safeOverlay,
                    reason: stringValue(item["reason"])
                )
            )
        }

        // Append any missing indices so we never drop local winners.
        for index in 0..<imageCount where !seen.contains(index) {
            picks.append(
                OpenAIVisionThumbnailPick(
                    localIndex: index,
                    overlayText: "",
                    reason: "Kept as local alternative"
                )
            )
        }

        guard !picks.isEmpty else { throw ServiceError.emptyResult }
        return OpenAIVisionThumbnailPlan(picks: picks)
    }

    static func stringValue(_ any: Any?) -> String {
        (any as? String)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
    }

    static func stringArray(_ any: Any?) -> [String] {
        (any as? [Any] ?? []).compactMap { item in
            let value = (item as? String)?
                .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            return value.isEmpty ? nil : value
        }
    }

    static func intValue(_ any: Any?) -> Int? {
        if let value = any as? Int { return value }
        if let value = any as? Double { return Int(value) }
        if let value = any as? String { return Int(value) }
        return nil
    }

    // MARK: - Audio helpers

    static func extractCompressedAudio(from videoURL: URL) async throws -> URL {
        guard let ffmpegPath = ProductionPassService.ffmpegPath else {
            throw ServiceError.ffmpegMissing
        }

        let outputURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("HughesClipPrep-OpenAI-\(UUID().uuidString).mp3")
        let logURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("HughesClipPrep-OpenAI-\(UUID().uuidString).log")
        FileManager.default.createFile(atPath: logURL.path, contents: nil)

        let arguments = [
            "-hide_banner", "-loglevel", "warning", "-y",
            "-i", videoURL.path,
            "-vn", "-ac", "1", "-ar", "16000",
            "-b:a", "48k",
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

    private static func exportAudioChunk(
        from audioURL: URL,
        start: TimeInterval,
        duration: TimeInterval
    ) async throws -> URL {
        guard let ffmpegPath = ProductionPassService.ffmpegPath else {
            throw ServiceError.ffmpegMissing
        }

        let outputURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("HughesClipPrep-OpenAI-Chunk-\(UUID().uuidString).mp3")
        let logURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("HughesClipPrep-OpenAI-Chunk-\(UUID().uuidString).log")
        FileManager.default.createFile(atPath: logURL.path, contents: nil)

        let arguments = [
            "-hide_banner", "-loglevel", "error", "-y",
            "-ss", String(format: "%.3f", start),
            "-i", audioURL.path,
            "-t", String(format: "%.3f", duration),
            "-ac", "1", "-ar", "16000", "-b:a", "48k",
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

    private static func audioDuration(of url: URL) async throws -> TimeInterval {
        let asset = AVURLAsset(url: url)
        let duration = CMTimeGetSeconds((try? await asset.load(.duration)) ?? .zero)
        return duration.isFinite ? duration : 0
    }

    private static func runProcess(
        executablePath: String,
        arguments: [String],
        logURL: URL
    ) async throws -> Int32 {
        try await withCheckedThrowingContinuation { continuation in
            do {
                let handle = try FileHandle(forWritingTo: logURL)
                let process = Process()
                process.executableURL = URL(fileURLWithPath: executablePath)
                process.arguments = arguments
                process.standardOutput = handle
                process.standardError = handle
                process.terminationHandler = { proc in
                    try? handle.close()
                    continuation.resume(returning: proc.terminationStatus)
                }
                try process.run()
            } catch {
                continuation.resume(throwing: error)
            }
        }
    }
}
