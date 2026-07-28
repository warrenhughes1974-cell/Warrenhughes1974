import SwiftUI

struct AnalysisView: View {
    @State private var viewModel = AnalysisViewModel()

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
        .navigationTitle("Smart Analysis")
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Smart Analysis")
                .font(.largeTitle.bold())
            Text("Scan a folder and review clip metadata. Speech, motion, and recommendations will fill in as we add detectors.")
                .foregroundStyle(.secondary)
        }
    }

    private var toolbar: some View {
        HStack(spacing: 12) {
            Button("Choose Folder") {
                viewModel.chooseFolder()
            }
            .disabled(viewModel.isScanning)

            Button("Rescan") {
                viewModel.rescan()
            }
            .disabled(viewModel.selectedFolderURL == nil || viewModel.isScanning)

            if viewModel.isScanning {
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
                        Text(result.video.fileName)
                    }
                    TableColumn("Duration") { result in
                        Text(result.video.formattedDuration)
                            .monospacedDigit()
                    }
                    TableColumn("Size") { result in
                        Text(result.video.formattedFileSize)
                    }
                    TableColumn("Speech") { result in
                        statusText(result.speechStatus)
                    }
                    TableColumn("Motion") { result in
                        statusText(result.motionStatus)
                    }
                    TableColumn("Recommendation") { result in
                        recommendationText(result.recommendation)
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
            Text("\(viewModel.results.count) clip(s)")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    @ViewBuilder
    private func statusText(_ status: AnalysisStatus) -> some View {
        switch status {
        case .pending, .running:
            Text(status.rawValue)
                .foregroundStyle(.orange)
        case .notImplemented:
            Text(status.rawValue)
                .foregroundStyle(.secondary)
        case .complete:
            Text(status.rawValue)
                .foregroundStyle(.green)
        case .failed:
            Text(status.rawValue)
                .foregroundStyle(.red)
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
    AnalysisView()
}
