import Foundation

/// Shared prompt + merge for cloud Shorts ranking / title polish.
enum ShortsCloudRefine {
    static func prompt(
        candidates: [ShortCandidate],
        transcript: Transcript,
        longFormTitle: String,
        brand: BrandSettingsValues,
        preset: BrandPreset
    ) -> String {
        var lines: [String] = []
        lines.append("You refine YouTube Shorts suggestions for a lifestyle/travel channel.")
        lines.append("Local splicing already chose the cut times — do NOT change start/end times or beats.")
        lines.append("Reorder the candidates by click-worthiness and rewrite each bestTitle.")
        lines.append("")
        lines.append("Channel: \(brand.channelPrefix.isEmpty ? brand.seriesName : brand.channelPrefix)")
        lines.append("Series preset: \(preset.displayName)")
        lines.append("Long-form title: \(longFormTitle.isEmpty ? "(none)" : longFormTitle)")
        lines.append("Channel context (spelling/identity only): \(brand.channelContext)")
        lines.append("")
        lines.append("Candidates (keep every id exactly once in your response):")

        for (offset, candidate) in candidates.enumerated() {
            lines.append(
                """
                [\(offset + 1)] id=\(candidate.id.uuidString)
                duration=\(Int(candidate.duration.rounded()))s score=\(String(format: "%.2f", candidate.score))
                range=\(candidate.formattedRange)
                currentTitle=\(candidate.bestTitle)
                quote=\(candidate.quote)
                story=\(candidate.storySummary)
                """
            )
        }

        lines.append("")
        lines.append("Transcript (for wording only):")
        lines.append(String(transcript.fullText.prefix(8_000)))
        lines.append("")
        lines.append(
            """
            Rules:
            - Return EVERY candidate id exactly once, best first.
            - bestTitle: short, punchy, grammatical, first person when the speaker is the traveler.
            - Do not invent people, pets on the trip, or places not supported by the quote/transcript.
            - Include #Shorts in each title (or it will be added for you).
            - Keep titles under ~90 characters before #Shorts.
            - rankScore is 0.0–1.0 (higher = better Short).

            Return ONLY JSON:
            {
              "ranked": [
                { "id": "UUID", "bestTitle": "Hook line #Shorts", "rankScore": 0.91 }
              ]
            }
            """
        )
        return lines.joined(separator: "\n")
    }

    static func apply(json: String, to candidates: [ShortCandidate]) throws -> [ShortCandidate] {
        guard let data = json.data(using: .utf8),
              let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw CloudAIClient.ServiceError.decodingFailed
        }

        let items = (root["ranked"] as? [[String: Any]])
            ?? (root["candidates"] as? [[String: Any]])
            ?? []

        guard !items.isEmpty else {
            throw CloudAIClient.ServiceError.emptyResult
        }

        let byID = Dictionary(uniqueKeysWithValues: candidates.map { ($0.id, $0) })
        var used = Set<UUID>()
        var refined: [ShortCandidate] = []

        for (offset, item) in items.enumerated() {
            let idString = OpenAIClient.stringValue(item["id"])
            guard let id = UUID(uuidString: idString),
                  let original = byID[id],
                  !used.contains(id) else {
                continue
            }

            let rawTitle = OpenAIClient.stringValue(item["bestTitle"])
            let title = rawTitle.isEmpty
                ? original.bestTitle
                : ShortsMetadataService.withShortsHashtag(rawTitle)

            let rankScore = (item["rankScore"] as? Double)
                ?? (item["rankScore"] as? Int).map(Double.init)
                ?? original.score

            // Blend local score with cloud rank so order can change without wiping local signal.
            let blended = min(max((original.score * 0.35) + (rankScore * 0.65), 0), 1)
            // Tiny tie-break so listed order wins when scores collide.
            let orderedScore = blended + Double(candidates.count - offset) * 0.0001

            refined.append(original.updating(bestTitle: title, score: orderedScore))
            used.insert(id)
        }

        // Append any candidates the model skipped, unchanged.
        for candidate in candidates where !used.contains(candidate.id) {
            refined.append(candidate)
        }

        guard !refined.isEmpty else {
            throw CloudAIClient.ServiceError.emptyResult
        }

        return refined.sorted { $0.score > $1.score }
    }
}
