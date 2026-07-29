import SwiftUI

struct CleanerView: View {

    @ObservedObject var viewModel: CleanerViewModel

    @AppStorage("cleaningPreset")
    private var savedPreset =
        CleaningPreset.balanced.rawValue

    @AppStorage("cleaningTrimMode")
    private var savedTrimMode =
        CleaningTrimMode.edgesOnly.rawValue

    @AppStorage("productionPassEnabled")
    private var productionPassEnabled = true

    @AppStorage("productionPassLongPause")
    private var productionPassLongPause =
        ProductionPassSettings.defaultLongPauseSeconds

    private var selectedPreset: CleaningPreset {
        CleaningPreset(
            rawValue: savedPreset
        ) ?? .balanced
    }

    private var selectedTrimMode: CleaningTrimMode {
        CleaningTrimMode(
            rawValue: savedTrimMode
        ) ?? .edgesOnly
    }

    private var productionPassSettings: ProductionPassSettings {
        ProductionPassSettings(
            isEnabled: productionPassEnabled,
            longPauseSeconds: productionPassLongPause
        )
    }

    var body: some View {
        VStack(spacing: 0) {
            header

            Divider()

            ScrollView {
                VStack(
                    alignment: .leading,
                    spacing: 22
                ) {
                    folderSection
                    inventorySection
                    settingsSection
                    processingSection
                    logSection
                }
                .padding(28)
            }
        }
        .alert(
            AppIdentity.name,
            isPresented:
                $viewModel.showingError
        ) {
            Button(
                "OK",
                role: .cancel
            ) {}
        } message: {
            Text(
                viewModel.errorMessage
            )
        }
    }

    private var header: some View {
        HStack(spacing: 16) {
            Image(
                systemName:
                    "flag.checkered.2.crossed"
            )
            .font(.system(size: 34))
            .foregroundStyle(AppTheme.papaya)

            VStack(
                alignment: .leading,
                spacing: 3
            ) {
                Text(
                    AppIdentity.name
                )
                .font(.largeTitle)
                .fontWeight(.bold)
                .foregroundStyle(AppTheme.carbon)

                Text(
                    AppIdentity.tagline
                )
                .foregroundStyle(
                    .secondary
                )
            }

            Spacer()

            if viewModel.autoEditorPath != nil {
                Label(
                    "Auto-Editor Ready",
                    systemImage:
                        "checkmark.circle.fill"
                )
                .foregroundStyle(.green)
            } else {
                Label(
                    "Auto-Editor Missing",
                    systemImage:
                        "exclamationmark.triangle.fill"
                )
                .foregroundStyle(.orange)
            }

            if productionPassEnabled {
                if viewModel.ffmpegPath != nil {
                    Label(
                        "FFmpeg Ready",
                        systemImage:
                            "checkmark.circle.fill"
                    )
                    .foregroundStyle(.green)
                } else {
                    Label(
                        "FFmpeg Missing",
                        systemImage:
                            "exclamationmark.triangle.fill"
                    )
                    .foregroundStyle(.orange)
                }
            }
        }
        .padding(.horizontal, 28)
        .padding(.vertical, 22)
        .background(AppTheme.softBlue)
    }

    private var folderSection: some View {
        GroupBox {
            VStack(
                alignment: .leading,
                spacing: 14
            ) {
                HStack {
                    Image(
                        systemName: "folder"
                    )
                    .font(.title2)

                    Text(
                        viewModel
                            .selectedFolderPath
                    )
                    .lineLimit(1)
                    .truncationMode(.middle)
                    .textSelection(.enabled)

                    Spacer()

                    Button(
                        "Choose Folder"
                    ) {
                        viewModel
                            .chooseFolder()
                    }
                    .disabled(
                        viewModel.isProcessing ||
                        viewModel.isScanning
                    )
                }

                HStack {
                    if viewModel.isScanning {
                        ProgressView()
                            .controlSize(.small)
                    }

                    Text(
                        viewModel
                            .statusMessage
                    )
                    .foregroundStyle(
                        .secondary
                    )

                    Spacer()

                    if !viewModel.videos.isEmpty {
                        Button("Rescan") {
                            viewModel
                                .scanFolder()
                        }
                        .disabled(
                            viewModel.isScanning ||
                            viewModel.isProcessing
                        )
                    }
                }
            }
            .padding(4)
        } label: {
            Label(
                "Source Folder",
                systemImage:
                    "folder.badge.plus"
            )
            .font(.headline)
        }
    }

    private var inventorySection: some View {
        GroupBox {
            VStack(spacing: 0) {
                if viewModel.videos.isEmpty {
                    ContentUnavailableView(
                        "No Videos Loaded",
                        systemImage:
                            "video.slash",
                        description: Text(
                            "Choose a folder containing MP4, MOV, or M4V files."
                        )
                    )
                    .frame(height: 260)
                } else {
                    HStack {
                        statistic(
                            title: "Videos",
                            value:
                                "\(viewModel.videos.count)"
                        )

                        Divider()
                            .frame(height: 42)

                        statistic(
                            title:
                                "Total Footage",
                            value:
                                viewModel
                                    .formattedTotalDuration
                        )

                        Divider()
                            .frame(height: 42)

                        statistic(
                            title: "Output",
                            value:
                                "Processed folder"
                        )

                        Spacer()
                    }
                    .padding(.vertical, 12)

                    Divider()

                    List(
                        viewModel.videos
                    ) { video in
                        HStack(spacing: 12) {
                            Image(
                                systemName: "film"
                            )
                            .foregroundStyle(
                                .secondary
                            )

                            VStack(alignment: .leading, spacing: 2) {
                                Text(video.name)
                                    .lineLimit(1)

                                Text(video.formattedRecordedAt)
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }

                            Spacer()

                            Text(
                                video
                                    .formattedFileSize
                            )
                            .foregroundStyle(
                                .secondary
                            )
                            .frame(
                                width: 90,
                                alignment:
                                    .trailing
                            )

                            Text(
                                video
                                    .formattedDuration
                            )
                            .monospacedDigit()
                            .frame(
                                width: 75,
                                alignment:
                                    .trailing
                            )
                        }
                    }
                    .frame(height: 260)
                }
            }
        } label: {
            Label(
                "Video Inventory",
                systemImage:
                    "list.bullet.rectangle"
            )
            .font(.headline)
        }
    }

    private func statistic(
        title: String,
        value: String
    ) -> some View {
        VStack(
            alignment: .leading,
            spacing: 3
        ) {
            Text(title)
                .font(.caption)
                .foregroundStyle(
                    .secondary
                )

            Text(value)
                .font(.headline)
        }
        .frame(
            minWidth: 130,
            alignment: .leading
        )
    }

    private var settingsSection: some View {
        GroupBox {
            VStack(
                alignment: .leading,
                spacing: 14
            ) {
                Picker(
                    "Trim Mode",
                    selection: $savedTrimMode
                ) {
                    ForEach(
                        CleaningTrimMode.allCases
                    ) { mode in
                        Text(mode.rawValue)
                            .tag(mode.rawValue)
                    }
                }
                .pickerStyle(.segmented)
                .disabled(
                    viewModel.isProcessing
                )

                Text(
                    selectedTrimMode.explanation
                )
                .foregroundStyle(
                    .secondary
                )
                .font(.callout)

                Picker(
                    "Cutting Style",
                    selection: $savedPreset
                ) {
                    ForEach(
                        CleaningPreset.allCases
                    ) { preset in
                        Text(preset.rawValue)
                            .tag(
                                preset.rawValue
                            )
                    }
                }
                .pickerStyle(.segmented)
                .disabled(
                    viewModel.isProcessing
                )

                HStack {
                    Text(
                        selectedPreset
                            .explanation
                    )
                    .foregroundStyle(
                        .secondary
                    )

                    Spacer()

                    Text(
                        String(
                            format:
                                "%.2f-second edge margin",
                            selectedPreset
                                .marginSeconds
                        )
                    )
                    .fontWeight(.semibold)
                }

                Divider()

                Toggle(
                    "Production Pass",
                    isOn: $productionPassEnabled
                )
                .disabled(
                    viewModel.isProcessing
                )

                Text(
                    "After edge trim: light denoise, loudness normalize, and remove awkward pauses longer than the threshold below."
                )
                .foregroundStyle(
                    .secondary
                )
                .font(.callout)

                if productionPassEnabled {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text("Remove pauses longer than")
                                .fontWeight(.semibold)
                            Spacer()
                            Text(
                                String(
                                    format: "%.1f sec",
                                    productionPassLongPause
                                )
                            )
                            .monospacedDigit()
                            .foregroundStyle(.secondary)
                        }

                        Slider(
                            value: $productionPassLongPause,
                            in: 1.0...5.0,
                            step: 0.5
                        )
                        .disabled(
                            viewModel.isProcessing
                        )

                        Text(
                            "Short natural pauses stay. Only long dead air in the middle gets cut."
                        )
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    }
                }

                Divider()

                Label(
                    "Original videos are never modified or deleted.",
                    systemImage:
                        "lock.shield"
                )
                .foregroundStyle(
                    .secondary
                )

                Label(
                    "Existing _CLEANED files are skipped automatically.",
                    systemImage:
                        "arrow.triangle.2.circlepath"
                )
                .foregroundStyle(
                    .secondary
                )
            }
            .padding(4)
        } label: {
            Label(
                "Cleaning Settings",
                systemImage:
                    "slider.horizontal.3"
            )
            .font(.headline)
        }
    }

    private var processingSection: some View {
        GroupBox {
            VStack(
                alignment: .leading,
                spacing: 14
            ) {
                HStack {
                    if viewModel.isProcessing {
                        Button(
                            "Cancel Processing",
                            role: .destructive
                        ) {
                            viewModel
                                .cancelProcessing()
                        }
                        .disabled(
                            viewModel.isCancelling
                        )
                    } else {
                        Button {
                            viewModel
                                .startProcessing(
                                    using:
                                        selectedPreset,
                                    trimMode:
                                        selectedTrimMode,
                                    productionPass:
                                        productionPassSettings
                                )
                        } label: {
                            Label(
                                "Start Processing",
                                systemImage:
                                    "play.fill"
                            )
                        }
                        .buttonStyle(
                            .borderedProminent
                        )
                        .tint(AppTheme.papaya)
                        .disabled(
                            viewModel
                                .selectedFolderURL
                                == nil ||
                            viewModel
                                .videos
                                .isEmpty ||
                            viewModel
                                .isScanning
                        )
                    }

                    Button {
                        viewModel
                            .openOutputFolder()
                    } label: {
                        Label(
                            "Open Processed Folder",
                            systemImage:
                                "folder"
                        )
                    }
                    .disabled(
                        viewModel
                            .selectedFolderURL
                            == nil
                    )

                    Spacer()

                    Text(
                        "Elapsed: \(viewModel.formattedElapsedTime)"
                    )
                    .monospacedDigit()
                    .foregroundStyle(
                        .secondary
                    )
                }

                ProgressView(
                    value: viewModel.progress
                )
                .progressViewStyle(.linear)

                HStack {
                    if viewModel.isProcessing {
                        Text(
                            "\(viewModel.currentIndex + 1) of \(viewModel.videos.count)"
                        )
                        .fontWeight(
                            .semibold
                        )

                        Text(
                            viewModel
                                .currentFileName
                        )
                        .lineLimit(1)
                        .truncationMode(
                            .middle
                        )
                        .foregroundStyle(
                            .secondary
                        )
                    } else {
                        Text(
                            viewModel
                                .statusMessage
                        )
                        .foregroundStyle(
                            .secondary
                        )
                    }

                    Spacer()
                }

                HStack(spacing: 22) {
                    resultCount(
                        title: "Processed",
                        value:
                            viewModel
                                .processedCount,
                        symbol:
                            "checkmark.circle"
                    )

                    resultCount(
                        title: "Skipped",
                        value:
                            viewModel
                                .skippedCount,
                        symbol:
                            "forward.circle"
                    )

                    resultCount(
                        title: "Failed",
                        value:
                            viewModel
                                .failedCount,
                        symbol:
                            "xmark.circle"
                    )
                }
            }
            .padding(4)
        } label: {
            Label(
                "Processing",
                systemImage:
                    "gearshape.2"
            )
            .font(.headline)
        }
    }

    private func resultCount(
        title: String,
        value: Int,
        symbol: String
    ) -> some View {
        Label(
            "\(title): \(value)",
            systemImage: symbol
        )
        .foregroundStyle(.secondary)
    }

    private var logSection: some View {
        GroupBox {
            ScrollView {
                Text(
                    viewModel.logText.isEmpty
                    ? "Activity will appear here."
                    : viewModel.logText
                )
                .font(
                    .system(
                        .caption,
                        design: .monospaced
                    )
                )
                .textSelection(.enabled)
                .frame(
                    maxWidth: .infinity,
                    alignment: .topLeading
                )
                .padding(8)
            }
            .frame(height: 180)
            .background(
                Color(
                    nsColor:
                        .textBackgroundColor
                )
            )
            .clipShape(
                RoundedRectangle(
                    cornerRadius: 6
                )
            )
        } label: {
            Label(
                "Activity Log",
                systemImage: "doc.text"
            )
            .font(.headline)
        }
    }
}

#Preview {
    CleanerView(viewModel: CleanerViewModel())
}
