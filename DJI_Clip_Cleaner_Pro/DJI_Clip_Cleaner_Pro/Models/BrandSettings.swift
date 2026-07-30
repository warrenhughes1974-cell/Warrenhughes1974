import Foundation
import Observation

struct BrandSettingsValues: Sendable {
    let channelPrefix: String
    let seriesName: String
    let defaultHook: String
    let titleFormat: BrandTitleFormat
    let usePinkTitles: Bool
    let titlePinkRed: Double
    let titlePinkGreen: Double
    let titlePinkBlue: Double
    let titleScale: Double
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

    static let minimumTitleScale = 0.6
    static let maximumTitleScale = 1.6

    private init() {
        load()
    }

    var values: BrandSettingsValues {
        BrandSettingsValues(
            channelPrefix: channelPrefix.trimmingCharacters(in: .whitespacesAndNewlines),
            seriesName: seriesName.trimmingCharacters(in: .whitespacesAndNewlines),
            defaultHook: defaultHook.trimmingCharacters(in: .whitespacesAndNewlines),
            titleFormat: titleFormat,
            usePinkTitles: usePinkTitles,
            titlePinkRed: titlePinkRed,
            titlePinkGreen: titlePinkGreen,
            titlePinkBlue: titlePinkBlue,
            titleScale: titleScale
        )
    }

    func applyColorSwatch(_ swatch: ThumbnailColorSwatch) {
        usePinkTitles = true
        titlePinkRed = swatch.red
        titlePinkGreen = swatch.green
        titlePinkBlue = swatch.blue
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
            "seriesName": seriesName,
            "defaultHook": defaultHook,
            "selectedPreset": selectedPreset.rawValue,
            "titleFormat": titleFormat.rawValue,
            "usePinkTitles": usePinkTitles,
            "titlePinkRed": titlePinkRed,
            "titlePinkGreen": titlePinkGreen,
            "titlePinkBlue": titlePinkBlue,
            "titleScale": titleScale
        ]

        UserDefaults.standard.set(payload, forKey: Self.storageKey)
    }

    func load() {
        guard let payload = UserDefaults.standard.dictionary(forKey: Self.storageKey) else {
            return
        }

        channelPrefix = payload["channelPrefix"] as? String ?? channelPrefix
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
    }
}
