import Foundation

struct OpenAISettingsValues: Sendable {
    let useWhisper: Bool
    let useCloudStory: Bool
    let useCloudCopy: Bool
    let useVisionThumbnails: Bool
    let model: String
}

/// Cloud AI preferences. The API key lives in a locked local file
/// (Application Support), not UserDefaults or Keychain.
@MainActor
@Observable
final class OpenAISettings {
    static let shared = OpenAISettings()

    private static let storageKey = "HughesClipPrep.OpenAISettings"

    var useWhisper = true
    var useCloudStory = true
    var useCloudCopy = true
    /// GPT Vision reranks thumbnail frames and suggests overlay text.
    var useVisionThumbnails = true
    /// Cheap default; user can switch to gpt-4o in Settings for stronger copy.
    var model = "gpt-4o-mini"

    /// Draft field for the Settings SecureField (not persisted as plain text).
    var apiKeyDraft = ""

    /// In-memory cache so UI / prep steps do not re-hit disk on every read.
    private var cachedAPIKey: String?

    private init() {
        load()
        cachedAPIKey = KeychainStore.get(service: KeychainStore.Service.openAIAPIKey)
    }

    var values: OpenAISettingsValues {
        OpenAISettingsValues(
            useWhisper: useWhisper,
            useCloudStory: useCloudStory,
            useCloudCopy: useCloudCopy,
            useVisionThumbnails: useVisionThumbnails,
            model: model.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                ? "gpt-4o-mini"
                : model.trimmingCharacters(in: .whitespacesAndNewlines)
        )
    }

    var hasAPIKey: Bool {
        !(resolvedAPIKey() ?? "").isEmpty
    }

    var apiKeyPreview: String {
        guard let key = resolvedAPIKey(), key.count > 8 else {
            return "No key saved"
        }
        return "Saved · \(key.prefix(7))…\(key.suffix(4))"
    }

    func apiKey() -> String? {
        resolvedAPIKey()
    }

    func saveAPIKeyFromDraft() -> Bool {
        let trimmed = apiKeyDraft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmed.hasPrefix("sk-"), trimmed.count > 20 else {
            return false
        }
        let ok = KeychainStore.set(trimmed, service: KeychainStore.Service.openAIAPIKey)
        if ok {
            cachedAPIKey = trimmed
            apiKeyDraft = ""
            save()
        }
        return ok
    }

    func clearAPIKey() {
        KeychainStore.delete(service: KeychainStore.Service.openAIAPIKey)
        cachedAPIKey = nil
        apiKeyDraft = ""
        save()
    }

    func save() {
        let payload: [String: Any] = [
            "useWhisper": useWhisper,
            "useCloudStory": useCloudStory,
            "useCloudCopy": useCloudCopy,
            "useVisionThumbnails": useVisionThumbnails,
            "model": model
        ]
        UserDefaults.standard.set(payload, forKey: Self.storageKey)
    }

    private func resolvedAPIKey() -> String? {
        if let cachedAPIKey, !cachedAPIKey.isEmpty {
            return cachedAPIKey
        }
        let loaded = KeychainStore.get(service: KeychainStore.Service.openAIAPIKey)
        cachedAPIKey = loaded
        return loaded
    }

    private func load() {
        guard let payload = UserDefaults.standard.dictionary(forKey: Self.storageKey) else {
            return
        }
        useWhisper = payload["useWhisper"] as? Bool ?? useWhisper
        useCloudStory = payload["useCloudStory"] as? Bool ?? useCloudStory
        useCloudCopy = payload["useCloudCopy"] as? Bool ?? useCloudCopy
        useVisionThumbnails = payload["useVisionThumbnails"] as? Bool ?? useVisionThumbnails
        model = payload["model"] as? String ?? model
    }
}
