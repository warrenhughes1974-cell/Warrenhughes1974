import Foundation
import Security

/// Local secret storage for the OpenAI API key.
///
/// Desktop Update rebuilds change the app’s code signature, which makes macOS
/// Keychain prompt for the login password (and “Always Allow” often fails to
/// stick). We therefore keep the key in Application Support with 0600 perms
/// and only use Keychain to clean up any leftover item from older versions.
enum KeychainStore {
    enum Service {
        static let openAIAPIKey = "HughesClipPrep.OpenAI.APIKey"
        static let geminiAPIKey = "HughesClipPrep.Gemini.APIKey"
    }

    private static var supportDirectory: URL {
        let base = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        ).first!
        return base.appendingPathComponent(AppIdentity.desktopFolderName, isDirectory: true)
    }

    private static func fileURL(for service: String) -> URL {
        let name: String
        switch service {
        case Service.openAIAPIKey:
            name = "openai_api_key"
        case Service.geminiAPIKey:
            name = "gemini_api_key"
        default:
            name = service.replacingOccurrences(of: ".", with: "_")
        }
        return supportDirectory.appendingPathComponent(name, isDirectory: false)
    }

    static func set(_ value: String, service: String) -> Bool {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return false }

        do {
            try FileManager.default.createDirectory(
                at: supportDirectory,
                withIntermediateDirectories: true
            )
            let url = fileURL(for: service)
            try Data(trimmed.utf8).write(to: url, options: [.atomic])
            try FileManager.default.setAttributes(
                [.posixPermissions: 0o600],
                ofItemAtPath: url.path
            )
            // Remove any pre-1.48 Keychain copy so macOS stops asking for access.
            deleteLegacyKeychainItem(service: service)
            return true
        } catch {
            return false
        }
    }

    static func get(service: String) -> String? {
        let url = fileURL(for: service)
        guard let data = try? Data(contentsOf: url),
              let value = String(data: data, encoding: .utf8)?
                .trimmingCharacters(in: .whitespacesAndNewlines),
              !value.isEmpty else {
            return nil
        }
        return value
    }

    static func delete(service: String) {
        let url = fileURL(for: service)
        try? FileManager.default.removeItem(at: url)
        deleteLegacyKeychainItem(service: service)
    }

    /// Best-effort cleanup. SecItemDelete should not show the password sheet.
    private static func deleteLegacyKeychainItem(service: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: "default"
        ]
        SecItemDelete(query as CFDictionary)
    }
}
