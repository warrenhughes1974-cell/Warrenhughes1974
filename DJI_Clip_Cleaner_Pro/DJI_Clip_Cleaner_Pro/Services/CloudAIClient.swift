import Foundation

/// Routes cloud AI calls to OpenAI or Google Gemini based on Settings.
enum CloudAIClient {
    enum ServiceError: LocalizedError {
        case missingAPIKey
        case emptyResult
        case decodingFailed
        case httpStatus(Int, String)
        case invalidResponse
        case ffmpegMissing
        case audioExtractFailed

        var errorDescription: String? {
            switch self {
            case .missingAPIKey:
                return "Add your cloud AI API key in Settings."
            case .emptyResult:
                return "Cloud AI returned an empty result."
            case .decodingFailed:
                return "Could not read the cloud AI response."
            case .httpStatus(let code, let body):
                return "Cloud AI request failed (\(code)): \(body)"
            case .invalidResponse:
                return "Cloud AI returned an unexpected response."
            case .ffmpegMissing:
                return "FFmpeg was not found. Install it with: brew install ffmpeg"
            case .audioExtractFailed:
                return "Could not extract audio for cloud transcription."
            }
        }
    }

    // MARK: - Transcription

    static func transcribe(
        videoURL: URL,
        provider: CloudAIProvider,
        apiKey: String
    ) async throws -> Transcript {
        switch provider {
        case .openAI:
            return try await OpenAIClient.transcribeWithWhisper(
                videoURL: videoURL,
                apiKey: apiKey
            )
        case .gemini:
            return try await GeminiClient.transcribe(
                videoURL: videoURL,
                apiKey: apiKey,
                model: "gemini-2.5-flash"
            )
        }
    }

    // MARK: - Story / copy

    static func analyzeStory(
        transcript: Transcript,
        existingHook: String,
        brand: BrandSettingsValues,
        provider: CloudAIProvider,
        model: String,
        apiKey: String
    ) async throws -> StoryAnalysis {
        switch provider {
        case .openAI:
            return try await OpenAIClient.analyzeStory(
                transcript: transcript,
                existingHook: existingHook,
                brand: brand,
                model: model,
                apiKey: apiKey
            )
        case .gemini:
            return try await GeminiClient.analyzeStory(
                transcript: transcript,
                existingHook: existingHook,
                brand: brand,
                model: model,
                apiKey: apiKey
            )
        }
    }

    static func generateUploadCopy(
        analysis: StoryAnalysis,
        title: String,
        brand: BrandSettingsValues,
        transcript: Transcript?,
        provider: CloudAIProvider,
        model: String,
        apiKey: String
    ) async throws -> OpenAIUploadCopy {
        switch provider {
        case .openAI:
            return try await OpenAIClient.generateUploadCopy(
                analysis: analysis,
                title: title,
                brand: brand,
                transcript: transcript,
                model: model,
                apiKey: apiKey
            )
        case .gemini:
            return try await GeminiClient.generateUploadCopy(
                analysis: analysis,
                title: title,
                brand: brand,
                transcript: transcript,
                model: model,
                apiKey: apiKey
            )
        }
    }

    // MARK: - Smart Analysis

    static func assistClipRecommendation(
        fileName: String,
        local: ClipRecommendation,
        localNotes: String,
        talkingPercent: Double,
        motionPercent: Double,
        durationSeconds: Double,
        jerkSummary: String,
        transcriptSnippet: String?,
        provider: CloudAIProvider,
        model: String,
        apiKey: String
    ) async throws -> OpenAIClipAssist {
        switch provider {
        case .openAI:
            return try await OpenAIClient.assistClipRecommendation(
                fileName: fileName,
                local: local,
                localNotes: localNotes,
                talkingPercent: talkingPercent,
                motionPercent: motionPercent,
                durationSeconds: durationSeconds,
                jerkSummary: jerkSummary,
                transcriptSnippet: transcriptSnippet,
                model: model,
                apiKey: apiKey
            )
        case .gemini:
            return try await GeminiClient.assistClipRecommendation(
                fileName: fileName,
                local: local,
                localNotes: localNotes,
                talkingPercent: talkingPercent,
                motionPercent: motionPercent,
                durationSeconds: durationSeconds,
                jerkSummary: jerkSummary,
                transcriptSnippet: transcriptSnippet,
                model: model,
                apiKey: apiKey
            )
        }
    }

    static func suggestCutHints(
        fileName: String,
        recommendation: ClipRecommendation,
        durationSeconds: Double,
        transcript: Transcript,
        provider: CloudAIProvider,
        model: String,
        apiKey: String
    ) async throws -> OpenAICutHints {
        switch provider {
        case .openAI:
            return try await OpenAIClient.suggestCutHints(
                fileName: fileName,
                recommendation: recommendation,
                durationSeconds: durationSeconds,
                transcript: transcript,
                model: model,
                apiKey: apiKey
            )
        case .gemini:
            return try await GeminiClient.suggestCutHints(
                fileName: fileName,
                recommendation: recommendation,
                durationSeconds: durationSeconds,
                transcript: transcript,
                model: model,
                apiKey: apiKey
            )
        }
    }

    // MARK: - Vision

    static func rankThumbnailFrames(
        jpegImages: [Data],
        storySummary: String,
        domain: String,
        currentOverlay: String,
        provider: CloudAIProvider,
        model: String,
        apiKey: String
    ) async throws -> OpenAIVisionThumbnailPlan {
        switch provider {
        case .openAI:
            return try await OpenAIClient.rankThumbnailFrames(
                jpegImages: jpegImages,
                storySummary: storySummary,
                domain: domain,
                currentOverlay: currentOverlay,
                model: model,
                apiKey: apiKey
            )
        case .gemini:
            return try await GeminiClient.rankThumbnailFrames(
                jpegImages: jpegImages,
                storySummary: storySummary,
                domain: domain,
                currentOverlay: currentOverlay,
                model: model,
                apiKey: apiKey
            )
        }
    }
}

// MARK: - Gemini

enum GeminiClient {
    private static let maxInlineBytes = 18 * 1_024 * 1_024

    static func transcribe(
        videoURL: URL,
        apiKey: String,
        model: String
    ) async throws -> Transcript {
        guard !apiKey.isEmpty else { throw CloudAIClient.ServiceError.missingAPIKey }

        let audioURL = try await OpenAIClient.extractCompressedAudio(from: videoURL)
        defer { try? FileManager.default.removeItem(at: audioURL) }

        let data = try Data(contentsOf: audioURL)
        guard !data.isEmpty else { throw CloudAIClient.ServiceError.audioExtractFailed }
        guard data.count <= maxInlineBytes else {
            // Long files: fall back to on-device rather than failing the whole run.
            return try await TranscriptionService.transcribe(videoURL: videoURL)
        }

        let prompt = """
        Transcribe this audio accurately. Return ONLY JSON:
        {
          "languageCode": "en",
          "fullText": "full transcript",
          "segments": [
            { "startSeconds": 0.0, "endSeconds": 2.5, "text": "words" }
          ]
        }
        Use short segments with real timestamps. Do not invent words that were not spoken.
        """

        let raw = try await generateJSON(
            model: model,
            apiKey: apiKey,
            system: "You are a precise transcription engine. JSON only.",
            userText: prompt,
            inlineParts: [
                (mimeType: "audio/mpeg", data: data)
            ]
        )
        return try decodeTranscript(from: raw)
    }

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

        let raw = try await generateJSON(
            model: model,
            apiKey: apiKey,
            system: "You are a factual YouTube story analyst. Return compact JSON only.",
            userText: prompt,
            inlineParts: []
        )
        return try OpenAIClient.decodeStoryAnalysis(from: raw)
    }

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
        let raw = try await generateJSON(
            model: model,
            apiKey: apiKey,
            system: "You write publish-ready YouTube metadata. JSON only. Never invent cast or places.",
            userText: prompt,
            inlineParts: []
        )
        return try OpenAIClient.decodeUploadCopy(from: raw)
    }

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

        let raw = try await generateJSON(
            model: model,
            apiKey: apiKey,
            system: "You are a clip triage assistant. JSON only. Never invent facts.",
            userText: prompt,
            inlineParts: []
        )
        return try OpenAIClient.decodeClipAssist(from: raw)
    }

    static func suggestCutHints(
        fileName: String,
        recommendation: ClipRecommendation,
        durationSeconds: Double,
        transcript: Transcript,
        model: String,
        apiKey: String
    ) async throws -> OpenAICutHints {
        let timed = OpenAIClient.timedTranscriptBlock(from: transcript, maxChars: 2_800)
        guard !timed.isEmpty else { throw CloudAIClient.ServiceError.emptyResult }

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

        let raw = try await generateJSON(
            model: model,
            apiKey: apiKey,
            system: "You suggest edit cut hints from transcripts. JSON only. Never invent facts.",
            userText: prompt,
            inlineParts: []
        )
        return try OpenAIClient.decodeCutHints(from: raw, durationSeconds: durationSeconds)
    }

    static func rankThumbnailFrames(
        jpegImages: [Data],
        storySummary: String,
        domain: String,
        currentOverlay: String,
        model: String,
        apiKey: String
    ) async throws -> OpenAIVisionThumbnailPlan {
        guard !jpegImages.isEmpty else { throw CloudAIClient.ServiceError.emptyResult }

        var parts: [(mimeType: String, data: Data)] = []
        var text = """
        You are a YouTube thumbnail director for a real travel/vlog channel.
        Rank these \(jpegImages.count) frames from best to worst click-through.
        Prefer emotion, clear subject, strong composition, and story fit.
        Avoid blurry, dull, empty, or face-filling frames.

        Story type: \(domain)
        Story summary: \(storySummary)
        Current overlay idea: \(currentOverlay)

        Images follow in order (image 1 = index 0). Include every image exactly once, best first.
        Return ONLY JSON:
        {
          "picks": [
            { "index": 0, "overlayText": "2 TO 4 WORDS", "reason": "short reason" }
          ]
        }
        Never invent people who are not on this trip.
        """

        // Gemini multimodal: text then images.
        _ = text
        for (offset, jpeg) in jpegImages.enumerated() {
            text += "\n[Image \(offset + 1) index \(offset)]"
            parts.append((mimeType: "image/jpeg", data: jpeg))
        }

        let raw = try await generateJSON(
            model: model,
            apiKey: apiKey,
            system: "You pick clickable YouTube thumbnails. JSON only.",
            userText: text,
            inlineParts: parts
        )
        return try OpenAIClient.decodeVisionPlan(from: raw, imageCount: jpegImages.count)
    }

    // MARK: - HTTP

    private static func generateJSON(
        model: String,
        apiKey: String,
        system: String,
        userText: String,
        inlineParts: [(mimeType: String, data: Data)]
    ) async throws -> String {
        let encodedModel = model.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? model
        guard let url = URL(
            string: "https://generativelanguage.googleapis.com/v1beta/models/\(encodedModel):generateContent"
        ) else {
            throw CloudAIClient.ServiceError.invalidResponse
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(apiKey, forHTTPHeaderField: "x-goog-api-key")
        request.timeoutInterval = 180

        var userParts: [[String: Any]] = [
            ["text": userText]
        ]
        for part in inlineParts {
            userParts.append([
                "inline_data": [
                    "mime_type": part.mimeType,
                    "data": part.data.base64EncodedString()
                ]
            ])
        }

        let body: [String: Any] = [
            "systemInstruction": [
                "parts": [["text": system]]
            ],
            "contents": [
                [
                    "role": "user",
                    "parts": userParts
                ]
            ],
            "generationConfig": [
                "temperature": 0.3,
                "responseMimeType": "application/json"
            ]
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw CloudAIClient.ServiceError.invalidResponse
        }
        guard (200...299).contains(http.statusCode) else {
            let bodyText = String(data: data, encoding: .utf8) ?? ""
            throw CloudAIClient.ServiceError.httpStatus(http.statusCode, String(bodyText.prefix(280)))
        }

        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let candidates = root["candidates"] as? [[String: Any]],
              let content = candidates.first?["content"] as? [String: Any],
              let parts = content["parts"] as? [[String: Any]] else {
            throw CloudAIClient.ServiceError.invalidResponse
        }

        let text = parts.compactMap { $0["text"] as? String }.joined()
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { throw CloudAIClient.ServiceError.emptyResult }
        return text
    }

    private static func decodeTranscript(from json: String) throws -> Transcript {
        guard let data = json.data(using: .utf8),
              let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw CloudAIClient.ServiceError.decodingFailed
        }

        let fullText = OpenAIClient.stringValue(root["fullText"])
        let language = OpenAIClient.stringValue(root["languageCode"]).isEmpty
            ? "en"
            : OpenAIClient.stringValue(root["languageCode"])

        var segments: [TranscriptSegment] = []
        if let items = root["segments"] as? [[String: Any]] {
            for item in items {
                let text = OpenAIClient.stringValue(item["text"])
                guard !text.isEmpty else { continue }
                let start = (item["startSeconds"] as? Double)
                    ?? (item["start"] as? Double)
                    ?? 0
                let end = (item["endSeconds"] as? Double)
                    ?? (item["end"] as? Double)
                    ?? (start + 1)
                let duration = max(end - start, 0.2)
                segments.append(
                    TranscriptSegment(
                        text: text,
                        startTime: max(start, 0),
                        duration: duration
                    )
                )
            }
        }

        let resolvedFull = fullText.isEmpty
            ? segments.map(\.text).joined(separator: " ")
            : fullText
        guard !resolvedFull.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw CloudAIClient.ServiceError.emptyResult
        }

        if segments.isEmpty {
            segments = [
                TranscriptSegment(text: resolvedFull, startTime: 0, duration: 1)
            ]
        }

        return Transcript(
            fullText: resolvedFull,
            segments: segments,
            languageCode: language,
            usedOnDevice: false
        )
    }
}
