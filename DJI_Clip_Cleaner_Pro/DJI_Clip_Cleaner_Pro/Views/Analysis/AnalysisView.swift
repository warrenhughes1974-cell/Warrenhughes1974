import SwiftUI

struct AnalysisView: View {
    @ObservedObject var cleanerViewModel: CleanerViewModel
    @Binding var selectedTab: Int

    @State private var viewModel = AnalysisViewModel()
    @State private var showingSettings = false
    @State private var showingPipelineConfirm = false

    @AppStorage("cleaningPreset")
    private var savedPreset = CleaningPreset.balanced.rawValue

    @AppStorage("cleaningTrimMode")
    private var savedTrimMode = CleaningTrimMode.edgesOnly.rawValue

    @AppStorage("productionPassEnabled")
    private var productionPassEnabled = true

    @AppStorage("productionPassLongPause")
    private var productionPassLongPause =
        ProductionPassSettings.defaultLongPauseSeconds

    @AppStorage("stabilizationEnabled")
    private var stabilizationEnabled = false

    private var selectedPreset: CleaningPreset {
        CleaningPreset(rawValue: savedPreset) ?? .balanced
    }

    private var selectedTrimMode: CleaningTrimMode {
        CleaningTrimMode(rawValue: savedTrimMode) ?? .edgesOnly
    }

    private var productionPassSettings: ProductionPassSettings {
        ProductionPassSettings(
            isEnabled: productionPassEnabled,
            longPauseSeconds: productionPassLongPause
        )
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            header
            toolbar
            if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .foregroundStyle(.red)
                    .font(.callout)
            }
            resultsTable
            footer
        }
        .padding(20)
        .sheet(isPresented: $showingSettings) {
            SettingsView()
                .frame(minWidth: 520, minHeight: 640)
        }
        .confirmationDialog(
            "Run Pipeline?",
            isPresented: $showingPipelineConfirm,
            titleVisibility: .visible
        ) {
            Button("Run Pipeline") {
                viewModel.runPipeline(
                    cleanerViewModel: cleanerViewModel,
                    preset: selectedPreset,
                    trimMode: selectedTrimMode,
                    productionPass: productionPassSettings,
                    stabilize: stabilizationEnabled
                ) {
                    selectedTab = 0
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text(
                """
                1. Move DISCARD clips to _DISCARD folder
                2. Leave REVIEW clips in place
                3. Send KEEP clips to Clip Cleaner and start processing

                \(viewModel.pipelineSummary)
                """
            )
        }
    }

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 10) {
                    Text("Smart Analysis")
                        .font(.largeTitle.bold())
                        .foregroundStyle(AppTheme.carbon)

                    Text("v\(AppIdentity.version)")
                        .font(.caption.bold())
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(AppTheme.softOrange)
                        .foregroundStyle(AppTheme.papaya)
                        .clipShape(Capsule())
                }

                Text("Scan a folder to detect talking, motion, and keep/review/discard recommendations.")
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Button {
                showingSettings = true
            } label: {
                Label("Settings", systemImage: "gearshape")
            }
            .buttonStyle(.bordered)
            .tint(AppTheme.mclarenBlue)
        }
    }

    private var toolbar: some View {
        HStack(spacing: 12) {
            Button {
                viewModel.rescan()
            } label: {
                Label("Scan Folder", systemImage: "arrow.clockwise.circle.fill")
            }
            .buttonStyle(.borderedProminent)
            .tint(AppTheme.papaya)
            .controlSize(.large)

            Button("Change Folder…") {
                viewModel.chooseFolder()
            }
            .buttonStyle(.bordered)

            Button("Export CSV") {
                viewModel.exportReport()
            }
            .buttonStyle(.bordered)

            Button("Run Pipeline") {
                if viewModel.prepareRunPipeline() {
                    showingPipelineConfirm = true
                }
            }
            .buttonStyle(.bordered)

            if viewModel.isAnalyzing {
                Button("Cancel", role: .destructive) {
                    viewModel.cancelAnalysis()
                }
                .buttonStyle(.bordered)
            }

            if viewModel.isScanning || viewModel.isAnalyzing {
                ProgressView()
                    .controlSize(.small)
            }

            Spacer()

            if let folder = viewModel.selectedFolderURL {
                Text(folder.path)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                    .truncationMode(.middle)
            }
        }
    }

    private var resultsTable: some View {
        Group {
            if viewModel.results.isEmpty {
                ContentUnavailableView(
                    "No Clips Loaded",
                    systemImage: "film",
                    description: Text(viewModel.statusMessage)
                )
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                Table(viewModel.results) {
                    TableColumn("Clip") { result in
                        Text(result.video.name)
                    }
                    TableColumn("Recorded") { result in
                        Text(result.video.formattedRecordedAt)
                            .font(.caption)
                    }
                    TableColumn("Duration") { result in
                        Text(result.video.formattedDuration)
                            .monospacedDigit()
                    }
                    TableColumn("Speech") { result in
                        summaryText(
                            result.speechSummary,
                            status: result.speechStatus
                        )
                    }
                    TableColumn("Motion") { result in
                        summaryText(
                            result.motionSummary,
                            status: result.motionStatus
                        )
                    }
                    TableColumn("Recommendation") { result in
                        recommendationText(result.recommendation)
                    }
                    TableColumn("Reason") { result in
                        Text(result.notes)
                            .foregroundStyle(.secondary)
                            .lineLimit(2)
                    }
                }
            }
        }
    }

    private var footer: some View {
        HStack {
            Text(viewModel.statusMessage)
                .font(.caption)
                .foregroundStyle(.secondary)
            Spacer()
            Text("\(viewModel.results.count) clip(s) · v\(AppIdentity.version)")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    @ViewBuilder
    private func summaryText(_ summary: String, status: AnalysisStatus) -> some View {
        switch status {
        case .running, .pending:
            Text(summary)
                .foregroundStyle(.orange)
        case .failed:
            Text(summary)
                .foregroundStyle(.red)
        case .notImplemented:
            Text(summary)
                .foregroundStyle(.secondary)
        case .complete:
            if summary.contains("Silent") || summary.contains("Static") {
                Text(summary)
                    .foregroundStyle(.secondary)
            } else {
                Text(summary)
                    .foregroundStyle(Color.green)
            }
        }
    }

    @ViewBuilder
    private func recommendationText(_ recommendation: ClipRecommendation) -> some View {
        switch recommendation {
        case .keep:
            Text(recommendation.rawValue).foregroundStyle(.green).bold()
        case .review:
            Text(recommendation.rawValue).foregroundStyle(.orange).bold()
        case .discard:
            Text(recommendation.rawValue).foregroundStyle(.red).bold()
        default:
            Text(recommendation.rawValue).foregroundStyle(.secondary)
        }
    }
}

#Preview {
    AnalysisView(
        cleanerViewModel: CleanerViewModel(),
        selectedTab: .constant(1)
    )
}
