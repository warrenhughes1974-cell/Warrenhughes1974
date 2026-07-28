import Foundation

enum FolderScannerError: LocalizedError {
    case accessDenied(URL)
    case unreadable(URL)

    var errorDescription: String? {
        switch self {
        case .accessDenied(let url):
            return "Cannot access folder: \(url.path)"
        case .unreadable(let url):
            return "Cannot read folder contents: \(url.path)"
        }
    }
}

struct FolderScanner {
    private static let supportedExtensions: Set<String> = ["mp4", "mov", "m4v", "mts", "m2ts"]

    static func scanVideos(in folderURL: URL) throws -> [URL] {
        let didStartAccess = folderURL.startAccessingSecurityScopedResource()
        defer {
            if didStartAccess {
                folderURL.stopAccessingSecurityScopedResource()
            }
        }

        guard FileManager.default.isReadableFile(atPath: folderURL.path) else {
            throw FolderScannerError.unreadable(folderURL)
        }

        let keys: [URLResourceKey] = [.isRegularFileKey, .isDirectoryKey]
        let contents = try FileManager.default.contentsOfDirectory(
            at: folderURL,
            includingPropertiesForKeys: keys,
            options: [.skipsHiddenFiles]
        )

        return contents
            .filter { url in
                let ext = url.pathExtension.lowercased()
                guard Self.supportedExtensions.contains(ext) else { return false }
                let values = try? url.resourceValues(forKeys: [.isRegularFileKey])
                return values?.isRegularFile == true
            }
            .sorted { $0.lastPathComponent.localizedStandardCompare($1.lastPathComponent) == .orderedAscending }
    }
}
