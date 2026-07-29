import AppKit
import AVFoundation
import Combine
import Foundation

@MainActor
final class CleanerViewModel: ObservableObject {

    @Published var selectedFolderURL: URL?
    @Published var selectedFolderPath = "No folder selected"
    @Published var videos: [VideoFile] = []
    @Published var isScanning = false

    @Published var isProcessing = false
    @Published var isCancelling = false
    @Published var currentFileName = ""
    @Published var currentIndex = 0

    @Published var processedCount = 0
    @Published var skippedCount = 0
    @Published var failedCount = 0

    @Published var progress = 0.0
    @Published var elapsedTime: TimeInterval = 0

    @Published var statusMessage =
        "Choose a folder containing your video clips."

    @Published var logText = ""

    @Published var showingError = false
    @Published var errorMessage = ""

    private var activeProcess: Process?
    private var processingQueue: [VideoFile] = []
    private var activePreset: CleaningPreset = .balanced
    private var activeTrimMode: CleaningTrimMode = .edgesOnly
    private var activeProductionPass = ProductionPassSettings.enabledByDefault
    private var processingStartedAt: Date?
    private var elapsedTimer: Timer?
    private var cancellationRequested = false
    private var currentOutputURL: URL?

    private let supportedExtensions = [
        "mp4",
        "mov",
        "m4v"
    ]

    var totalDuration: TimeInterval {
        videos.reduce(0) { result, video in
            result + video.duration
        }
    }

    var formattedTotalDuration: String {
        VideoFile.formatDuration(totalDuration)
    }

    var formattedElapsedTime: String {
        VideoFile.formatDuration(elapsedTime)
    }

    var ffmpegPath: String? {
        ProductionPassService.ffmpegPath
    }

    var outputFolderURL: URL? {
        selectedFolderURL?.appendingPathComponent(
            "Processed",
            isDirectory: true
        )
    }

    var autoEditorPath: String? {
        let candidates = [
            "/opt/homebrew/bin/auto-editor",
            "/usr/local/bin/auto-editor"
        ]

        return candidates.first {
            FileManager.default.isExecutableFile(
                atPath: $0
            )
        }
    }

    func chooseFolder() {
        guard !isProcessing else {
            return
        }

        let panel = NSOpenPanel()

        panel.title = "Choose a Video Folder"
        panel.message =
            "Select the folder containing your original video clips."
        panel.prompt = "Choose Folder"
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.canCreateDirectories = false
        panel.resolvesAliases = true

        if panel.runModal() == .OK,
           let folderURL = panel.url {

            selectedFolderURL = folderURL
            selectedFolderPath = folderURL.path

            scanFolder()
        }
    }

    func receivePipelineHandoff(
        folder: URL,
        videos: [VideoFile],
        summary: String
    ) {
        guard !isProcessing else {
            return
        }

        selectedFolderURL = folder
        selectedFolderPath = folder.path
        self.videos = VideoFile.sortByCaptureDate(videos)

        statusMessage =
            "\(videos.count) KEEP clip(s) loaded from Smart Analysis pipeline."

        appendLog("")
        appendLog("==================================================")
        appendLog("PIPELINE HANDOFF")
        appendLog("==================================================")
        appendLog(summary)
        appendLog("KEEP clips queued: \(videos.count)")
        appendLog("")
    }

    func scanFolder() {
        guard let folderURL = selectedFolderURL else {
            return
        }

        guard !isProcessing else {
            return
        }

        isScanning = true
        videos = []
        statusMessage = "Scanning folder…"

        appendLog(
            "Scanning: \(folderURL.path)"
        )

        Task {
            let discoveredVideos =
                await loadVideos(from: folderURL)

            videos = VideoFile.sortByCaptureDate(discoveredVideos)

            isScanning = false

            if videos.isEmpty {
                statusMessage =
                    "No supported MP4, MOV, or M4V videos were found."

                appendLog(
                    "Scan completed: no supported videos found."
                )
            } else {
                statusMessage =
                    "\(videos.count) videos found — \(formattedTotalDuration) total footage."

                appendLog(
                    "Scan completed: \(videos.count) videos, \(formattedTotalDuration)."
                )
            }
        }
    }

    private func loadVideos(
        from folderURL: URL
    ) async -> [VideoFile] {

        let fileManager = FileManager.default

        guard let fileURLs =
                try? fileManager.contentsOfDirectory(
                    at: folderURL,
                    includingPropertiesForKeys: [
                        .isRegularFileKey,
                        .fileSizeKey
                    ],
                    options: [
                        .skipsHiddenFiles,
                        .skipsPackageDescendants
                    ]
                ) else {
            return []
        }

        var results: [VideoFile] = []

        for fileURL in fileURLs {
            let fileExtension =
                fileURL.pathExtension.lowercased()

            guard supportedExtensions.contains(
                fileExtension
            ) else {
                continue
            }

            let values =
                try? fileURL.resourceValues(
                    forKeys: [
                        .isRegularFileKey,
                        .fileSizeKey
                    ]
                )

            guard values?.isRegularFile == true else {
                continue
            }

            let asset = AVURLAsset(url: fileURL)

            do {
                let durationValue =
                    try await asset.load(.duration)

                let duration =
                    CMTimeGetSeconds(durationValue)

                guard duration.isFinite,
                      duration > 0 else {
                    continue
                }

                let video = VideoFile(
                    url: fileURL,
                    duration: duration,
                    fileSize: Int64(
                        values?.fileSize ?? 0
                    )
                )

                results.append(video)
            } catch {
                appendLog(
                    "Could not read \(fileURL.lastPathComponent): \(error.localizedDescription)"
                )
            }
        }

        return results
    }

    func startProcessing(
        using preset: CleaningPreset,
        trimMode: CleaningTrimMode,
        productionPass: ProductionPassSettings
    ) {
        guard !isProcessing else {
            return
        }

        guard let autoEditorPath else {
            showError(
                """
                Auto-Editor could not be found.

                Expected location:
                /opt/homebrew/bin/auto-editor

                Open Terminal and confirm it is installed by running:

                auto-editor --version
                """
            )

            return
        }

        if productionPass.isEnabled, ffmpegPath == nil {
            showError(
                """
                Production Pass needs FFmpeg.

                Install it with:

                brew install ffmpeg
                """
            )

            return
        }

        guard let selectedFolderURL else {
            showError(
                "Choose a video folder first."
            )

            return
        }

        guard !videos.isEmpty else {
            showError(
                "No supported videos are available to process."
            )

            return
        }

        let outputFolder =
            selectedFolderURL.appendingPathComponent(
                "Processed",
                isDirectory: true
            )

        do {
            try FileManager.default.createDirectory(
                at: outputFolder,
                withIntermediateDirectories: true
            )
        } catch {
            showError(
                """
                The Processed folder could not be created.

                \(error.localizedDescription)
                """
            )

            return
        }

        resetProcessingState()

        isProcessing = true
        cancellationRequested = false
        processingQueue = videos
        activePreset = preset
        activeTrimMode = trimMode
        activeProductionPass = productionPass
        processingStartedAt = Date()

        startElapsedTimer()

        appendLog("")
        appendLog(
            "=================================================="
        )
        appendLog("DJI Clip Cleaner Pro")
        appendLog(
            "=================================================="
        )
        appendLog(
            "Videos queued: \(videos.count)"
        )
        appendLog(
            "Preset: \(preset.rawValue)"
        )
        appendLog(
            "Trim mode: \(trimMode.rawValue)"
        )
        appendLog(
            String(
                format: "Edge margin: %.2f seconds",
                preset.marginSeconds
            )
        )
        if productionPass.isEnabled {
            appendLog("Production Pass: ON")
            appendLog(
                String(
                    format: "Long pause trim: %.1f seconds",
                    productionPass.longPauseSeconds
                )
            )
            appendLog(
                "Production tools: denoise, loudness normalize, long-pause trim"
            )
            if let ffmpegPath {
                appendLog("FFmpeg: \(ffmpegPath)")
            }
        } else {
            appendLog("Production Pass: OFF")
        }
        appendLog(
            "Auto-Editor: \(autoEditorPath)"
        )
        appendLog(
            "Output: \(outputFolder.path)"
        )
        appendLog(
            "Original files will not be changed."
        )
        appendLog("")

        statusMessage =
            "Preparing to process \(videos.count) videos…"

        processNextVideo(
            autoEditorPath: autoEditorPath,
            outputFolder: outputFolder
        )
    }

    private func processNextVideo(
        autoEditorPath: String,
        outputFolder: URL
    ) {
        guard isProcessing else {
            return
        }

        if cancellationRequested {
            finishProcessing(cancelled: true)
            return
        }

        guard currentIndex <
                processingQueue.count else {

            finishProcessing(cancelled: false)
            return
        }

        let video =
            processingQueue[currentIndex]

        currentFileName = video.name

        progress =
            Double(currentIndex) /
            Double(
                max(processingQueue.count, 1)
            )

        statusMessage =
            "Processing \(currentIndex + 1) of \(processingQueue.count): \(video.name)"

        let baseName =
            video.url
                .deletingPathExtension()
                .lastPathComponent

        let fileExtension =
            video.url.pathExtension

        let outputURL =
            outputFolder.appendingPathComponent(
                "\(baseName)_CLEANED.\(fileExtension)"
            )

        currentOutputURL = outputURL

        if FileManager.default.fileExists(
            atPath: outputURL.path
        ) {
            skippedCount += 1

            appendLog(
                "[SKIPPED] \(video.name) — cleaned output already exists."
            )

            currentIndex += 1

            processNextVideo(
                autoEditorPath: autoEditorPath,
                outputFolder: outputFolder
            )

            return
        }

        appendLog(
            "[START] \(video.name) (\(video.formattedDuration))"
        )

        Task {
            let arguments = await buildAutoEditorArguments(
                for: video,
                outputURL: outputURL
            )

            await MainActor.run {
                self.runAutoEditor(
                    video: video,
                    arguments: arguments,
                    outputURL: outputURL,
                    autoEditorPath: autoEditorPath,
                    outputFolder: outputFolder
                )
            }
        }
    }

    private func buildAutoEditorArguments(
        for video: VideoFile,
        outputURL: URL
    ) async -> [String] {
        let margin = String(
            format: "%.2fsec",
            activePreset.marginSeconds
        )

        switch activeTrimMode {
        case .fullClip:
            return [
                video.url.path,
                "--margin",
                margin,
                "--output",
                outputURL.path
            ]

        case .edgesOnly:
            if let boundaries = await SpeechAnalyzer.detectSpeechBoundaries(
                videoURL: video.url
            ) {
                let protectedRange = String(
                    format: "nil,%.2fsec,%.2fsec",
                    boundaries.firstSpeechTime,
                    boundaries.lastSpeechTime
                )

                appendLog(
                    String(
                        format: "[EDGES] Protecting speech from %.1fs to %.1fs",
                        boundaries.firstSpeechTime,
                        boundaries.lastSpeechTime
                    )
                )

                return [
                    video.url.path,
                    "--when-inactive",
                    "cut",
                    "--margin",
                    margin,
                    "--set-action",
                    protectedRange,
                    "--output",
                    outputURL.path
                ]
            }

            appendLog(
                "[WARN] \(video.name) — no speech detected for edge trim; using full-clip mode."
            )

            return [
                video.url.path,
                "--margin",
                margin,
                "--output",
                outputURL.path
            ]
        }
    }

    private func runAutoEditor(
        video: VideoFile,
        arguments: [String],
        outputURL: URL,
        autoEditorPath: String,
        outputFolder: URL
    ) {
        guard isProcessing else {
            return
        }

        let process = Process()

        process.executableURL =
            URL(fileURLWithPath: autoEditorPath)
        process.arguments = arguments

        let temporaryLogURL =
            FileManager.default.temporaryDirectory
                .appendingPathComponent(
                    "DJIClipCleaner-\(UUID().uuidString).log"
                )

        FileManager.default.createFile(
            atPath: temporaryLogURL.path,
            contents: nil
        )

        guard let outputHandle =
                try? FileHandle(
                    forWritingTo: temporaryLogURL
                ) else {

            failedCount += 1

            appendLog(
                "[FAILED] \(video.name) — could not create temporary process log."
            )

            currentIndex += 1

            processNextVideo(
                autoEditorPath: autoEditorPath,
                outputFolder: outputFolder
            )

            return
        }

        process.standardOutput = outputHandle
        process.standardError = outputHandle

        activeProcess = process

        process.terminationHandler = {
            [weak self] completedProcess in

            try? outputHandle.close()

            let processOutput =
                (try? String(
                    contentsOf: temporaryLogURL,
                    encoding: .utf8
                )) ?? ""

            try? FileManager.default.removeItem(
                at: temporaryLogURL
            )

            Task { @MainActor in
                guard let self else {
                    return
                }

                self.activeProcess = nil

                if self.cancellationRequested {
                    self.removeIncompleteOutputIfNeeded()
                    self.finishProcessing(
                        cancelled: true
                    )

                    return
                }

                let outputExists =
                    FileManager.default.fileExists(
                        atPath: outputURL.path
                    )

                if completedProcess.terminationStatus == 0,
                   outputExists {

                    if self.activeProductionPass.isEnabled {
                        self.appendLog(
                            "[PRODUCTION] Polishing \(video.name)..."
                        )

                        do {
                            try await ProductionPassService.apply(
                                to: outputURL,
                                settings: self.activeProductionPass
                            )

                            self.appendLog(
                                "[PRODUCTION] Audio polish complete."
                            )
                        } catch {
                            self.failedCount += 1
                            self.removeIncompleteOutputIfNeeded()

                            self.appendLog(
                                "[FAILED] Production pass for \(video.name) — \(error.localizedDescription)"
                            )

                            self.currentIndex += 1
                            self.progress =
                                Double(self.currentIndex) /
                                Double(
                                    max(
                                        self.processingQueue.count,
                                        1
                                    )
                                )

                            self.processNextVideo(
                                autoEditorPath: autoEditorPath,
                                outputFolder: outputFolder
                            )

                            return
                        }
                    }

                    self.processedCount += 1

                    self.appendLog(
                        "[DONE] \(video.name)"
                    )
                } else {
                    self.failedCount += 1
                    self.removeIncompleteOutputIfNeeded()

                    self.appendLog(
                        "[FAILED] \(video.name) — exit code \(completedProcess.terminationStatus)"
                    )

                    let trimmedOutput =
                        processOutput
                            .trimmingCharacters(
                                in: .whitespacesAndNewlines
                            )

                    if !trimmedOutput.isEmpty {
                        self.appendLog(
                            trimmedOutput
                        )
                    }
                }

                self.currentIndex += 1

                self.progress =
                    Double(self.currentIndex) /
                    Double(
                        max(
                            self.processingQueue.count,
                            1
                        )
                    )

                self.processNextVideo(
                    autoEditorPath: autoEditorPath,
                    outputFolder: outputFolder
                )
            }
        }

        do {
            try process.run()
        } catch {
            try? outputHandle.close()

            try? FileManager.default.removeItem(
                at: temporaryLogURL
            )

            activeProcess = nil
            failedCount += 1

            appendLog(
                "[FAILED] \(video.name) — \(error.localizedDescription)"
            )

            currentIndex += 1

            processNextVideo(
                autoEditorPath: autoEditorPath,
                outputFolder: outputFolder
            )
        }
    }

    func cancelProcessing() {
        guard isProcessing else {
            return
        }

        cancellationRequested = true
        isCancelling = true

        statusMessage =
            "Cancelling the current process…"

        appendLog(
            "Cancellation requested."
        )

        if let activeProcess,
           activeProcess.isRunning {

            activeProcess.terminate()

            DispatchQueue.main.asyncAfter(
                deadline: .now() + 2
            ) { [weak self] in

                guard let self,
                      let activeProcess =
                        self.activeProcess,
                      activeProcess.isRunning else {
                    return
                }

                activeProcess.interrupt()
            }
        } else {
            finishProcessing(cancelled: true)
        }
    }

    private func finishProcessing(
        cancelled: Bool
    ) {
        stopElapsedTimer()

        activeProcess = nil
        currentOutputURL = nil
        isProcessing = false
        isCancelling = false
        currentFileName = ""

        if cancelled {
            statusMessage =
                "Processing cancelled. \(processedCount) videos completed."

            appendLog("")
            appendLog("PROCESSING CANCELLED")
        } else {
            progress = 1.0

            statusMessage =
                "Finished: \(processedCount) processed, \(skippedCount) skipped, \(failedCount) failed."

            appendLog("")
            appendLog("PROCESSING FINISHED")
        }

        appendLog(
            "Processed: \(processedCount)"
        )

        appendLog(
            "Skipped: \(skippedCount)"
        )

        appendLog(
            "Failed: \(failedCount)"
        )

        appendLog(
            "Elapsed time: \(formattedElapsedTime)"
        )

        appendLog(
            "=================================================="
        )

        writeLogFile()
    }

    private func resetProcessingState() {
        currentIndex = 0
        processedCount = 0
        skippedCount = 0
        failedCount = 0
        progress = 0
        elapsedTime = 0
        currentFileName = ""
        currentOutputURL = nil
        isCancelling = false
    }

    private func removeIncompleteOutputIfNeeded() {
        guard let currentOutputURL else {
            return
        }

        guard FileManager.default.fileExists(
            atPath: currentOutputURL.path
        ) else {
            return
        }

        try? FileManager.default.removeItem(
            at: currentOutputURL
        )
    }

    private func startElapsedTimer() {
        stopElapsedTimer()

        elapsedTimer =
            Timer.scheduledTimer(
                withTimeInterval: 1,
                repeats: true
            ) { [weak self] _ in
                Task { @MainActor in
                    guard let self,
                          let processingStartedAt =
                            self.processingStartedAt else {
                        return
                    }

                    self.elapsedTime =
                        Date().timeIntervalSince(
                            processingStartedAt
                        )
                }
            }
    }

    private func stopElapsedTimer() {
        elapsedTimer?.invalidate()
        elapsedTimer = nil
    }

    private func appendLog(
        _ message: String
    ) {
        let timestamp =
            DateFormatter.logTimestamp.string(
                from: Date()
            )

        if message.isEmpty {
            logText += "\n"
        } else {
            logText +=
                "[\(timestamp)] \(message)\n"
        }
    }

    private func writeLogFile() {
        guard let outputFolderURL else {
            return
        }

        let logURL =
            outputFolderURL.appendingPathComponent(
                "DJI_Clip_Cleaner_Log.txt"
            )

        do {
            try logText.write(
                to: logURL,
                atomically: true,
                encoding: .utf8
            )
        } catch {
            appendLog(
                "Could not write log file: \(error.localizedDescription)"
            )
        }
    }

    func openOutputFolder() {
        guard let outputFolderURL else {
            return
        }

        do {
            try FileManager.default.createDirectory(
                at: outputFolderURL,
                withIntermediateDirectories: true
            )

            NSWorkspace.shared.open(
                outputFolderURL
            )
        } catch {
            showError(
                """
                The output folder could not be opened.

                \(error.localizedDescription)
                """
            )
        }
    }

    private func showError(
        _ message: String
    ) {
        errorMessage = message
        showingError = true

        appendLog(
            "ERROR: \(message)"
        )
    }
}
