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
            titlePinkBlue: titlePinkBlue
        )
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
            "titlePinkBlue": titlePinkBlue
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
    }
}
