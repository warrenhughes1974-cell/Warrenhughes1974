import Foundation

enum CloudAIProvider: String, CaseIterable, Identifiable, Sendable {
    case openAI = "openai"
    case gemini = "gemini"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .openAI: return "OpenAI"
        case .gemini: return "Google Gemini"
        }
    }
}

struct OpenAISettingsValues: Sendable {
    let provider: CloudAIProvider
    let useWhisper: Bool
    let useCloudStory: Bool
    let useCloudCopy: Bool
    let useVisionThumbnails: Bool
    let useAIAssistAnalysis: Bool
    let useAICutHints: Bool
    let useCloudShortsRefine: Bool
    let model: String
}

/// Cloud AI preferences (OpenAI or Gemini). Keys live in locked local files.
@MainActor
@Observable
final class OpenAISettings {
    static let shared = OpenAISettings()

    private static let storageKey = "HughesClipPrep.OpenAISettings"

    /// Which cloud brain to use for toggles below.
    var provider: CloudAIProvider = .openAI

    var useWhisper = true
    var useCloudStory = true
    var useCloudCopy = true
    var useVisionThumbnails = true
    var useAIAssistAnalysis = false
    var useAICutHints = false
    /// After local Shorts splicing, reorder moments and polish titles via cloud AI.
    var useCloudShortsRefine = true

    /// OpenAI chat model when provider == .openAI
    var model = "gpt-4o-mini"
    /// Gemini model when provider == .gemini
    var geminiModel = "gemini-2.5-flash"

    var apiKeyDraft = ""

    private var cachedOpenAIKey: String?
    private var cachedGeminiKey: String?

    private init() {
        load()
        cachedOpenAIKey = KeychainStore.get(service: KeychainStore.Service.openAIAPIKey)
        cachedGeminiKey = KeychainStore.get(service: KeychainStore.Service.geminiAPIKey)
    }

    var values: OpenAISettingsValues {
        OpenAISettingsValues(
            provider: provider,
            useWhisper: useWhisper,
            useCloudStory: useCloudStory,
            useCloudCopy: useCloudCopy,
            useVisionThumbnails: useVisionThumbnails,
            useAIAssistAnalysis: useAIAssistAnalysis,
            useAICutHints: useAICutHints,
            useCloudShortsRefine: useCloudShortsRefine,
            model: activeModel
        )
    }

    var activeModel: String {
        switch provider {
        case .openAI:
            return model.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                ? "gpt-4o-mini"
                : model.trimmingCharacters(in: .whitespacesAndNewlines)
        case .gemini:
            return geminiModel.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                ? "gemini-2.5-flash"
                : geminiModel.trimmingCharacters(in: .whitespacesAndNewlines)
        }
    }

    var hasAPIKey: Bool {
        !(apiKey() ?? "").isEmpty
    }

    var apiKeyPreview: String {
        guard let key = apiKey(), key.count > 8 else {
            return "No \(provider.displayName) key saved"
        }
        return "\(provider.displayName) · \(key.prefix(7))…\(key.suffix(4))"
    }

    func apiKey() -> String? {
        switch provider {
        case .openAI:
            return resolvedOpenAIKey()
        case .gemini:
            return resolvedGeminiKey()
        }
    }

    func saveAPIKeyFromDraft() -> Bool {
        let trimmed = apiKeyDraft.trimmingCharacters(in: .whitespacesAndNewlines)
        switch provider {
        case .openAI:
            guard trimmed.hasPrefix("sk-"), trimmed.count > 20 else { return false }
            let ok = KeychainStore.set(trimmed, service: KeychainStore.Service.openAIAPIKey)
            if ok {
                cachedOpenAIKey = trimmed
                apiKeyDraft = ""
                save()
            }
            return ok
        case .gemini:
            // AI Studio keys commonly start with AIza; accept any long secret.
            guard trimmed.count >= 20 else { return false }
            let ok = KeychainStore.set(trimmed, service: KeychainStore.Service.geminiAPIKey)
            if ok {
                cachedGeminiKey = trimmed
                apiKeyDraft = ""
                save()
            }
            return ok
        }
    }

    func clearAPIKey() {
        switch provider {
        case .openAI:
            KeychainStore.delete(service: KeychainStore.Service.openAIAPIKey)
            cachedOpenAIKey = nil
        case .gemini:
            KeychainStore.delete(service: KeychainStore.Service.geminiAPIKey)
            cachedGeminiKey = nil
        }
        apiKeyDraft = ""
        save()
    }

    func save() {
        let payload: [String: Any] = [
            "provider": provider.rawValue,
            "useWhisper": useWhisper,
            "useCloudStory": useCloudStory,
            "useCloudCopy": useCloudCopy,
            "useVisionThumbnails": useVisionThumbnails,
            "useAIAssistAnalysis": useAIAssistAnalysis,
            "useAICutHints": useAICutHints,
            "useCloudShortsRefine": useCloudShortsRefine,
            "model": model,
            "geminiModel": geminiModel
        ]
        UserDefaults.standard.set(payload, forKey: Self.storageKey)
    }

    private func resolvedOpenAIKey() -> String? {
        if let cachedOpenAIKey, !cachedOpenAIKey.isEmpty { return cachedOpenAIKey }
        let loaded = KeychainStore.get(service: KeychainStore.Service.openAIAPIKey)
        cachedOpenAIKey = loaded
        return loaded
    }

    private func resolvedGeminiKey() -> String? {
        if let cachedGeminiKey, !cachedGeminiKey.isEmpty { return cachedGeminiKey }
        let loaded = KeychainStore.get(service: KeychainStore.Service.geminiAPIKey)
        cachedGeminiKey = loaded
        return loaded
    }

    private func load() {
        guard let payload = UserDefaults.standard.dictionary(forKey: Self.storageKey) else {
            return
        }
        if let raw = payload["provider"] as? String,
           let value = CloudAIProvider(rawValue: raw) {
            provider = value
        }
        useWhisper = payload["useWhisper"] as? Bool ?? useWhisper
        useCloudStory = payload["useCloudStory"] as? Bool ?? useCloudStory
        useCloudCopy = payload["useCloudCopy"] as? Bool ?? useCloudCopy
        useVisionThumbnails = payload["useVisionThumbnails"] as? Bool ?? useVisionThumbnails
        useAIAssistAnalysis = payload["useAIAssistAnalysis"] as? Bool ?? useAIAssistAnalysis
        useAICutHints = payload["useAICutHints"] as? Bool ?? useAICutHints
        useCloudShortsRefine = payload["useCloudShortsRefine"] as? Bool ?? useCloudShortsRefine
        model = payload["model"] as? String ?? model
        geminiModel = payload["geminiModel"] as? String ?? geminiModel
    }
}
