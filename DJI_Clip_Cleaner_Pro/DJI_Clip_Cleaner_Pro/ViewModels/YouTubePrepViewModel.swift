import Foundation
import Observation

#if canImport(AppKit)
import AppKit
#endif

@MainActor
@Observable
final class YouTubePrepViewModel {
    var selectedVideoURL: URL?
    var hook = ""
    var generatedTitle = ""
    var generatedDescription = ""
    var generatedTags = ""
    var thumbnailPath = ""
    var statusMessage = "Choose your finished Filmora video to start YouTube prep."
    var errorMessage: String?
    var isWorking = false

    private static let lastVideoPathKey = "youtubePrepLastVideoPath"

    init() {
        restoreLastVideoIfAvailable()
    }

    var canGenerate: Bool {
        selectedVideoURL != nil && !hook.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var titlePreview: String {
        let brand = BrandSettings.shared.values
        let trimmedHook = hook.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedHook.isEmpty else {
            return "Type a hook to preview your YouTube title."
        }

        return YouTubeMetadataService.buildTitle(hook: trimmedHook, brand: brand)
    }

    func chooseVideo() {
        #if canImport(AppKit)
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.prompt = "Choose Video"
        panel.message = "Select your finished export from Filmora."
        panel.allowedContentTypes = [.mpeg4Movie, .quickTimeMovie, .movie]

        if let selectedVideoURL {
            panel.directoryURL = selectedVideoURL.deletingLastPathComponent()
        } else if let lastPath = UserDefaults.standard.string(forKey: Self.lastVideoPathKey) {
            panel.directoryURL = URL(fileURLWithPath: lastPath).deletingLastPathComponent()
        }

        guard panel.runModal() == .OK, let url = panel.url else { return }

        selectedVideoURL = url
        UserDefaults.standard.set(url.path, forKey: Self.lastVideoPathKey)
        errorMessage = nil

        if hook.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            hook = YouTubeMetadataService.hookSuggestion(from: url)
        }

        statusMessage = "Ready to prep \(url.lastPathComponent) for YouTube."
        #endif
    }

    func generateThumbnail() {
        guard let selectedVideoURL, canGenerate else {
            errorMessage = "Choose a video and type a hook first."
            return
        }

        isWorking = true
        errorMessage = nil
        statusMessage = "Generating thumbnail..."

        Task {
            do {
                let brand = BrandSettings.shared.values
                let title = YouTubeMetadataService.buildTitle(hook: hook, brand: brand)
                let outputURL = thumbnailOutputURL(for: selectedVideoURL, title: title)

                try await ThumbnailService.generate(
                    from: selectedVideoURL,
                    title: title,
                    brand: brand,
                    outputURL: outputURL
                )

                thumbnailPath = outputURL.path
                generatedTitle = title
                statusMessage = "Thumbnail saved to \(outputURL.lastPathComponent)"
                #if canImport(AppKit)
                NSWorkspace.shared.activateFileViewerSelecting([outputURL])
                #endif
            } catch {
                errorMessage = error.localizedDescription
                statusMessage = "Thumbnail generation failed."
            }

            isWorking = false
        }
    }

    func generateDescription() {
        guard canGenerate else {
            errorMessage = "Choose a video and type a hook first."
            return
        }

        let brand = BrandSettings.shared.values
        let preset = BrandSettings.shared.selectedPreset
        let title = YouTubeMetadataService.buildTitle(hook: hook, brand: brand)

        generatedTitle = title
        generatedDescription = YouTubeMetadataService.generateDescription(
            title: title,
            hook: hook,
            brand: brand,
            preset: preset
        )
        errorMessage = nil
        statusMessage = "Description ready. Copy it or generate the full upload package."
    }

    func generateTags() {
        guard canGenerate else {
            errorMessage = "Choose a video and type a hook first."
            return
        }

        let brand = BrandSettings.shared.values
        let preset = BrandSettings.shared.selectedPreset

        generatedTags = YouTubeMetadataService.generateTags(
            hook: hook,
            brand: brand,
            preset: preset
        )
        errorMessage = nil
        statusMessage = "Tags ready. Copy them or generate the full upload package."
    }

    func generateUploadPackage() {
        guard let selectedVideoURL, canGenerate else {
            errorMessage = "Choose a video and type a hook first."
            return
        }

        if generatedDescription.isEmpty {
            generateDescription()
        }

        if generatedTags.isEmpty {
            generateTags()
        }

        isWorking = true
        errorMessage = nil
        statusMessage = "Building YouTube upload package..."

        Task {
            do {
                let brand = BrandSettings.shared.values
                let title = YouTubeMetadataService.buildTitle(hook: hook, brand: brand)
                generatedTitle = title

                if thumbnailPath.isEmpty {
                    let outputURL = thumbnailOutputURL(for: selectedVideoURL, title: title)
                    try await ThumbnailService.generate(
                        from: selectedVideoURL,
                        title: title,
                        brand: brand,
                        outputURL: outputURL
                    )
                    thumbnailPath = outputURL.path
                }

                let packageFolder = try YouTubeMetadataService.writeUploadPackage(
                    videoURL: selectedVideoURL,
                    title: title,
                    hook: hook,
                    description: generatedDescription,
                    tags: generatedTags,
                    thumbnailURL: URL(fileURLWithPath: thumbnailPath)
                )

                statusMessage = "Upload package saved to YouTube_Prep/."
                #if canImport(AppKit)
                NSWorkspace.shared.activateFileViewerSelecting([packageFolder])
                #endif
            } catch {
                errorMessage = error.localizedDescription
                statusMessage = "Could not create upload package."
            }

            isWorking = false
        }
    }

    func copyDescription() {
        #if canImport(AppKit)
        guard !generatedDescription.isEmpty else { return }
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(generatedDescription, forType: .string)
        statusMessage = "Description copied to clipboard."
        #endif
    }

    func copyTags() {
        #if canImport(AppKit)
        guard !generatedTags.isEmpty else { return }
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(generatedTags, forType: .string)
        statusMessage = "Tags copied to clipboard."
        #endif
    }

    private func thumbnailOutputURL(for videoURL: URL, title: String) -> URL {
        let folder = videoURL.deletingLastPathComponent().appendingPathComponent(
            YouTubeMetadataService.uploadFolderName,
            isDirectory: true
        )

        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)

        let baseName = videoURL.deletingPathExtension().lastPathComponent
        return folder.appendingPathComponent("\(baseName)_thumbnail.jpg")
    }

    private func restoreLastVideoIfAvailable() {
        guard let path = UserDefaults.standard.string(forKey: Self.lastVideoPathKey) else {
            return
        }

        guard FileManager.default.fileExists(atPath: path) else {
            return
        }

        selectedVideoURL = URL(fileURLWithPath: path)
        statusMessage = "Ready to prep \(URL(fileURLWithPath: path).lastPathComponent) again."
    }
}

#if canImport(AppKit)
import UniformTypeIdentifiers
#endif
