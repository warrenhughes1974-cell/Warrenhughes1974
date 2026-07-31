import Foundation
import Observation

struct BrandSettingsValues: Sendable {
    let channelPrefix: String
    let channelContext: String
    let seriesName: String
    let defaultHook: String
    let titleFormat: BrandTitleFormat
    let usePinkTitles: Bool
    let titlePinkRed: Double
    let titlePinkGreen: Double
    let titlePinkBlue: Double
    let titleScale: Double
    let thumbnailEmojis: [String]
    let emojiPosition: ThumbnailEmojiPosition
    let titleFont: ThumbnailTitleFont
    let useTextOutline: Bool
}

/// One-click thumbnail text colors. Each one is bright enough to survive the
/// black-and-white outline on a busy frame.
struct ThumbnailColorSwatch: Identifiable, Sendable {
    let id: String
    let name: String
    let red: Double
    let green: Double
    let blue: Double

    static let all: [ThumbnailColorSwatch] = [
        ThumbnailColorSwatch(id: "pink", name: "Pink", red: 1.0, green: 0.30, blue: 0.60),
        ThumbnailColorSwatch(id: "white", name: "White", red: 1.0, green: 1.0, blue: 1.0),
        ThumbnailColorSwatch(id: "papaya", name: "Papaya", red: 1.0, green: 0.53, blue: 0.0),
        ThumbnailColorSwatch(id: "yellow", name: "Yellow", red: 1.0, green: 0.85, blue: 0.10),
        ThumbnailColorSwatch(id: "lime", name: "Lime", red: 0.60, green: 1.0, blue: 0.20),
        ThumbnailColorSwatch(id: "cyan", name: "Cyan", red: 0.20, green: 0.90, blue: 1.0),
        ThumbnailColorSwatch(id: "blood", name: "Blood Red", red: 0.85, green: 0.10, blue: 0.12)
    ]
}

@MainActor
@Observable
final class BrandSettings {
    static let shared = BrandSettings()

    private static let storageKey = "HughesClipPrep.BrandSettings"

    var channelPrefix = "Hughes"
    var channelContext = """
    Identity/spelling only — not plot evidence. Warren and Tina host Fun Now Run Later. Gabie and Domi are family names. Coco, Penny, Ramsey, Sadie, Alani, and Ryder are pets/dogs (not people). Brianna is Warren's coworker (spelling). Never cast anyone as on-camera, traveling, or part of this video unless the transcript explicitly says so. Never invent a family-trip or lifestyle theme from these notes.
    """
    var seriesName = ""
    var defaultHook = ""
    var selectedPreset: BrandPreset = .custom
    var titleFormat: BrandTitleFormat = .full
    var usePinkTitles = true
    var titlePinkRed = 1.0
    var titlePinkGreen = 0.30
    var titlePinkBlue = 0.60

    /// Multiplier on the auto-fitted thumbnail text size. 1.0 is the size the
    /// app picks on its own; the range keeps text readable without overflowing.
    var titleScale = 1.0

    /// Up to two emoji symbols drawn onto every branded thumbnail.
    var thumbnailEmojis: [String] = []
    var emojiPosition: ThumbnailEmojiPosition = .topRight
    var titleFont: ThumbnailTitleFont = .impact
    /// Classic YouTube look: thick black outer ring + white inner ring around fill.
    var useTextOutline = true

    static let minimumTitleScale = 0.6
    static let maximumTitleScale = 1.6

    private init() {
        load()
    }

    var values: BrandSettingsValues {
        BrandSettingsValues(
            channelPrefix: channelPrefix.trimmingCharacters(in: .whitespacesAndNewlines),
            channelContext: channelContext.trimmingCharacters(in: .whitespacesAndNewlines),
            seriesName: seriesName.trimmingCharacters(in: .whitespacesAndNewlines),
            defaultHook: defaultHook.trimmingCharacters(in: .whitespacesAndNewlines),
            titleFormat: titleFormat,
            usePinkTitles: usePinkTitles,
            titlePinkRed: titlePinkRed,
            titlePinkGreen: titlePinkGreen,
            titlePinkBlue: titlePinkBlue,
            titleScale: titleScale,
            thumbnailEmojis: Array(thumbnailEmojis.prefix(ThumbnailEmojiOption.maximumSelection)),
            emojiPosition: emojiPosition,
            titleFont: titleFont,
            useTextOutline: useTextOutline
        )
    }

    func applyColorSwatch(_ swatch: ThumbnailColorSwatch) {
        usePinkTitles = true
        titlePinkRed = swatch.red
        titlePinkGreen = swatch.green
        titlePinkBlue = swatch.blue
        save()
    }

    func toggleThumbnailEmoji(_ symbol: String) {
        if let index = thumbnailEmojis.firstIndex(of: symbol) {
            thumbnailEmojis.remove(at: index)
        } else if thumbnailEmojis.count < ThumbnailEmojiOption.maximumSelection {
            thumbnailEmojis.append(symbol)
        } else {
            // Full — replace the oldest pick so a click always does something.
            thumbnailEmojis.removeFirst()
            thumbnailEmojis.append(symbol)
        }

        save()
    }

    func clearThumbnailEmojis() {
        thumbnailEmojis = []
        save()
    }

    var titleColor: (red: Double, green: Double, blue: Double) {
        if usePinkTitles {
            return (titlePinkRed, titlePinkGreen, titlePinkBlue)
        }

        return (1.0, 1.0, 1.0)
    }

    var sampleTitle: String {
        let hook = defaultHook.trimmingCharacters(in: .whitespacesAndNewlines)
        let previewHook = hook.isEmpty ? activePreset.sampleHook : hook

        return TitleSuggestionService.formatTitle(
            hook: previewHook,
            brand: values
        )
    }

    private var activePreset: BrandPreset {
        if selectedPreset == .custom {
            return .custom
        }

        return selectedPreset
    }

    func applyPreset(_ preset: BrandPreset) {
        selectedPreset = preset

        if preset != .custom {
            seriesName = preset.seriesName
        }

        save()
    }

    func save() {
        let payload: [String: Any] = [
            "channelPrefix": channelPrefix,
            "channelContext": channelContext,
            "seriesName": seriesName,
            "defaultHook": defaultHook,
            "selectedPreset": selectedPreset.rawValue,
            "titleFormat": titleFormat.rawValue,
            "usePinkTitles": usePinkTitles,
            "titlePinkRed": titlePinkRed,
            "titlePinkGreen": titlePinkGreen,
            "titlePinkBlue": titlePinkBlue,
            "titleScale": titleScale,
            "thumbnailEmojis": thumbnailEmojis,
            "emojiPosition": emojiPosition.rawValue,
            "titleFont": titleFont.rawValue,
            "useTextOutline": useTextOutline
        ]

        UserDefaults.standard.set(payload, forKey: Self.storageKey)
    }

    func load() {
        guard let payload = UserDefaults.standard.dictionary(forKey: Self.storageKey) else {
            return
        }

        channelPrefix = payload["channelPrefix"] as? String ?? channelPrefix
        channelContext = payload["channelContext"] as? String ?? channelContext
        seriesName = payload["seriesName"] as? String ?? seriesName
        defaultHook = payload["defaultHook"] as? String ?? defaultHook

        if let presetRaw = payload["selectedPreset"] as? String,
           let preset = BrandPreset(rawValue: presetRaw) {
            selectedPreset = preset
        }

        if let formatRaw = payload["titleFormat"] as? String,
           let format = BrandTitleFormat(rawValue: formatRaw) {
            titleFormat = format
        }

        usePinkTitles = payload["usePinkTitles"] as? Bool ?? usePinkTitles
        titlePinkRed = payload["titlePinkRed"] as? Double ?? titlePinkRed
        titlePinkGreen = payload["titlePinkGreen"] as? Double ?? titlePinkGreen
        titlePinkBlue = payload["titlePinkBlue"] as? Double ?? titlePinkBlue

        let storedScale = payload["titleScale"] as? Double ?? titleScale
        titleScale = min(max(storedScale, Self.minimumTitleScale), Self.maximumTitleScale)

        if let storedEmojis = payload["thumbnailEmojis"] as? [String] {
            let allowed = Set(ThumbnailEmojiOption.catalog.map(\.symbol))
            thumbnailEmojis = storedEmojis
                .filter { allowed.contains($0) }
                .prefix(ThumbnailEmojiOption.maximumSelection)
                .map { $0 }
        }

        if let positionRaw = payload["emojiPosition"] as? String,
           let position = ThumbnailEmojiPosition(rawValue: positionRaw) {
            emojiPosition = position
        }

        if let fontRaw = payload["titleFont"] as? String,
           let font = ThumbnailTitleFont(rawValue: fontRaw) {
            titleFont = font
        }

        useTextOutline = payload["useTextOutline"] as? Bool ?? useTextOutline
    }
}
