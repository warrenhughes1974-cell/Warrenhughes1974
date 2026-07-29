import Foundation

enum YouTubeMetadataService {
    static let uploadFolderName = "YouTube_Prep"

    static func buildTitle(hook: String, brand: BrandSettingsValues) -> String {
        TitleSuggestionService.formatTitle(hook: hook, brand: brand)
    }

    static func hookSuggestion(from videoURL: URL, fallbackSeries: String = "") -> String {
        let baseName = videoURL.deletingPathExtension().lastPathComponent
        let cleaned = baseName
            .replacingOccurrences(of: "_", with: " ")
            .replacingOccurrences(of: "-", with: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)

        guard !cleaned.isEmpty else {
            return fallbackSeries.isEmpty ? "New Video" : "\(fallbackSeries) Video"
        }

        return cleaned
            .split(separator: " ")
            .map { word in
                word.prefix(1).uppercased() + word.dropFirst().lowercased()
            }
            .joined(separator: " ")
    }

    static func generateDescription(
        title: String,
        hook: String,
        brand: BrandSettingsValues,
        preset: BrandPreset
    ) -> String {
        let channel = brand.channelPrefix.isEmpty ? "the channel" : brand.channelPrefix
        let series = brand.seriesName.isEmpty ? "video" : brand.seriesName
        let trimmedHook = hook.trimmingCharacters(in: .whitespacesAndNewlines)

        var lines: [String] = [
            title,
            "",
            descriptionLead(
                channel: channel,
                series: series,
                hook: trimmedHook,
                preset: preset
            ),
            "",
            callToAction(for: preset, channel: brand.channelPrefix),
            "",
            "—",
            "Edited in Filmora",
            "Shot on DJI"
        ]

        if !brand.channelPrefix.isEmpty {
            lines.append("")
            lines.append("Follow \(brand.channelPrefix) for more uploads.")
        }

        return lines.joined(separator: "\n")
    }

    static func generateTags(
        hook: String,
        brand: BrandSettingsValues,
        preset: BrandPreset
    ) -> String {
        let tags = tagList(hook: hook, brand: brand, preset: preset)
        return tags.joined(separator: ", ")
    }

    static func writeUploadPackage(
        videoURL: URL,
        title: String,
        hook: String,
        description: String,
        tags: String,
        thumbnailURL: URL?
    ) throws -> URL {
        let packageFolder = videoURL.deletingLastPathComponent().appendingPathComponent(
            uploadFolderName,
            isDirectory: true
        )

        try FileManager.default.createDirectory(
            at: packageFolder,
            withIntermediateDirectories: true
        )

        let baseName = safeFilename(from: title)

        try title.write(
            to: packageFolder.appendingPathComponent("\(baseName)_title.txt"),
            atomically: true,
            encoding: .utf8
        )

        try description.write(
            to: packageFolder.appendingPathComponent("\(baseName)_description.txt"),
            atomically: true,
            encoding: .utf8
        )

        try tags.write(
            to: packageFolder.appendingPathComponent("\(baseName)_tags.txt"),
            atomically: true,
            encoding: .utf8
        )

        if let thumbnailURL,
           FileManager.default.fileExists(atPath: thumbnailURL.path) {
            let destination = packageFolder.appendingPathComponent("\(baseName)_thumbnail.jpg")
            if FileManager.default.fileExists(atPath: destination.path) {
                try FileManager.default.removeItem(at: destination)
            }
            try FileManager.default.copyItem(at: thumbnailURL, to: destination)
        }

        return packageFolder
    }

    private static func descriptionLead(
        channel: String,
        series: String,
        hook: String,
        preset: BrandPreset
    ) -> String {
        switch preset {
        case .halloweenHunt:
            return "Join \(channel) for another Halloween store hunt. In this \(series.lowercased()), we explore \(hook) and see what spooky finds are hiding on the shelves."
        case .storeWalk:
            return "Walk the aisles with \(channel). In this \(series.lowercased()), we check out \(hook) and see what's worth a closer look."
        case .productReview:
            return "\(channel) gives an honest look at \(hook) in this \(series.lowercased())."
        case .behindTheScenes:
            return "Go behind the scenes with \(channel). This \(series.lowercased()) covers \(hook)."
        case .custom:
            return "In this \(series), \(channel) shares \(hook)."
        }
    }

    private static func callToAction(for preset: BrandPreset, channel: String) -> String {
        let name = channel.isEmpty ? "the channel" : channel

        switch preset {
        case .halloweenHunt:
            return "🎃 Like, comment, and subscribe to \(name) for more Halloween hunts and creepy store walks."
        case .storeWalk:
            return "🛒 Like, comment, and subscribe to \(name) for more store walks and shelf finds."
        case .productReview:
            return "⭐ Like, comment, and subscribe to \(name) for more honest reviews."
        case .behindTheScenes:
            return "🎬 Like, comment, and subscribe to \(name) for more behind-the-scenes uploads."
        case .custom:
            return "🔔 Like, comment, and subscribe to \(name) for more videos."
        }
    }

    private static func tagList(
        hook: String,
        brand: BrandSettingsValues,
        preset: BrandPreset
    ) -> [String] {
        var tags: [String] = []

        func appendUnique(_ value: String) {
            let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !trimmed.isEmpty else { return }

            let key = trimmed.lowercased()
            guard !tags.contains(where: { $0.lowercased() == key }) else { return }

            tags.append(trimmed)
        }

        appendUnique(brand.channelPrefix)
        appendUnique(brand.seriesName)
        appendUnique(hook)

        for tag in presetTags(preset) {
            appendUnique(tag)
        }

        for word in hook.split(separator: " ") where word.count > 3 {
            appendUnique(String(word))
        }

        return Array(tags.prefix(15))
    }

    private static func presetTags(_ preset: BrandPreset) -> [String] {
        switch preset {
        case .halloweenHunt:
            return [
                "halloween",
                "halloween hunt",
                "spooky",
                "store walk",
                "seasonal finds",
                "youtube shorts alternative"
            ]
        case .storeWalk:
            return [
                "store walk",
                "shopping",
                "aisle find",
                "retail",
                "shelf check",
                "what's new in stores"
            ]
        case .productReview:
            return [
                "product review",
                "honest review",
                "worth it",
                "first look",
                "buy or pass"
            ]
        case .behindTheScenes:
            return [
                "behind the scenes",
                "bts",
                "creator setup",
                "filmmaking",
                "youtube prep"
            ]
        case .custom:
            return [
                "vlog",
                "youtube",
                "new upload"
            ]
        }
    }

    private static func safeFilename(from title: String) -> String {
        let invalid = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "-_")).inverted
        let cleaned = title
            .components(separatedBy: invalid)
            .filter { !$0.isEmpty }
            .joined(separator: "_")

        return cleaned.isEmpty ? "youtube_upload" : String(cleaned.prefix(80))
    }
}
