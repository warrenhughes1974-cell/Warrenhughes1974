import SwiftUI

struct ShortsView: View {
    @State private var viewModel = ShortsViewModel()

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                header
                sourceSection
                momentsSection
                exportedSection
                checklistSection
                footer
            }
            .padding(24)
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 10) {
                Text("Shorts")
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

            Text("Pull the strongest moments out of a finished video and export them vertical for YouTube Shorts.")
                .foregroundStyle(.secondary)
        }
    }

    private var sourceSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 16) {
                HStack(spacing: 12) {
                    Button("Choose Video…") {
                        viewModel.chooseVideo()
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(AppTheme.papaya)

                    Button("Transcribe Speech") {
                        viewModel.transcribeVideo()
                    }
                    .buttonStyle(.bordered)
                    .disabled(!viewModel.canTranscribe)

                    Button("Find Moments") {
                        viewModel.findMoments()
                    }
                    .buttonStyle(.bordered)
                    .disabled(!viewModel.canAnalyze)

                    if viewModel.isAnalyzing || viewModel.isExporting || viewModel.isTranscribing {
                        ProgressView()
                            .controlSize(.small)
                    }

                    Spacer()
                }

                Text(viewModel.transcriptSummary)
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Toggle("Burn captions onto exported Shorts", isOn: $viewModel.burnCaptions)
                    .disabled(viewModel.transcript == nil)

                if let videoURL = viewModel.selectedVideoURL {
                    Text(videoURL.path)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                        .truncationMode(.middle)
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("Short Length")
                        .fontWeight(.semibold)

                    Picker("Short Length", selection: $viewModel.targetLength) {
                        ForEach(ShortsFinderService.TargetLength.allCases) { length in
                            Text(length.displayName).tag(length)
                        }
                    }
                    .pickerStyle(.segmented)

                    Text(viewModel.targetLength.guidance)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text("Long-Form Title")
                        .fontWeight(.semibold)

                    TextField("Creepy Aisle Find | Halloween Hunt", text: $viewModel.longFormTitle)
                        .textFieldStyle(.roundedBorder)

                    Text("Used in each Short's description so viewers can find the full video.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                if !viewModel.ffmpegInstalled {
                    Label(
                        "FFmpeg is not installed. Run: brew install ffmpeg",
                        systemImage: "exclamationmark.triangle.fill"
                    )
                    .font(.caption)
                    .foregroundStyle(.orange)
                }
            }
            .padding(4)
        } label: {
            Label("Source Video", systemImage: "film.stack")
                .font(.headline)
                .foregroundStyle(AppTheme.mclarenBlue)
        }
    }

    private var momentsSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                if viewModel.candidates.isEmpty {
                    Text("Choose a video and click Find Moments. Hughes Clip Prep ranks Shorts like an assistant — spoken hook, projected scores, and a best title for each.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(Array(viewModel.candidates.enumerated()), id: \.element.id) { index, candidate in
                        candidateRow(candidate, index: index + 1)
                    }

                    HStack {
                        Button("Export Selected Shorts") {
                            viewModel.exportSelected()
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(AppTheme.mclarenBlue)
                        .disabled(!viewModel.canExport)

                        Button("Open Shorts Folder") {
                            viewModel.revealShortsFolder()
                        }
                        .buttonStyle(.bordered)

                        Spacer()
                    }
                    .padding(.top, 4)
                }
            }
            .padding(4)
        } label: {
            Label("Suggested Moments", systemImage: "sparkles.rectangle.stack")
                .font(.headline)
        }
    }

    private func candidateRow(_ candidate: ShortCandidate, index: Int) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Toggle(
                "",
                isOn: Binding(
                    get: { viewModel.isSelected(candidate) },
                    set: { _ in viewModel.toggleSelection(candidate) }
                )
            )
            .labelsHidden()
            .padding(.top, 4)

            VStack(alignment: .leading, spacing: 8) {
                HStack(alignment: .firstTextBaseline, spacing: 10) {
                    Text("Short #\(index)")
                        .font(.headline)
                        .foregroundStyle(AppTheme.mclarenBlue)

                    Text(candidate.formattedDuration)
                        .font(.caption.weight(.bold))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(AppTheme.papaya.opacity(0.22))
                        .clipShape(Capsule())

                    Text(candidate.formattedRange)
                        .font(.caption)
                        .monospacedDigit()
                        .foregroundStyle(.secondary)

                    Spacer()
                }

                Text(candidate.hookLine.isEmpty ? candidate.reason : "“\(candidate.hookLine)”")
                    .font(.title3.weight(.semibold))
                    .foregroundStyle(AppTheme.brandPink)
                    .lineLimit(2)

                HStack(spacing: 16) {
                    scoreBadge(label: "Projected Hook", value: candidate.projectedHook)
                    scoreBadge(label: "Projected Retention", value: candidate.projectedRetention)
                }

                if !candidate.bestTitle.isEmpty {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Best title")
                            .font(.caption2.weight(.semibold))
                            .foregroundStyle(.secondary)
                        Text(candidate.bestTitle)
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(.primary)
                    }
                }

                if !candidate.quote.isEmpty, candidate.quote != candidate.hookLine {
                    Text(candidate.quote)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                }
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(viewModel.isSelected(candidate)
                      ? AppTheme.papaya.opacity(0.14)
                      : AppTheme.softOrange.opacity(0.45))
        )
    }

    private func scoreBadge(label: String, value: Int) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text("\(value)")
                .font(.title2.weight(.bold))
                .monospacedDigit()
                .foregroundStyle(value >= 90 ? AppTheme.papaya : AppTheme.mclarenBlue)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(AppTheme.carbon.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    @ViewBuilder
    private var exportedSection: some View {
        if !viewModel.exported.isEmpty {
            GroupBox {
                VStack(alignment: .leading, spacing: 10) {
                    ForEach(viewModel.exported) { result in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(result.outputURL.lastPathComponent)
                                .font(.callout.bold())
                            Text(result.title)
                                .font(.caption)
                                .foregroundStyle(AppTheme.brandPink)
                            Text("From \(result.candidate.formattedRange)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    Text("Shorts_upload_notes.txt in the same folder has the description and checklist for every clip.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(4)
            } label: {
                Label("Exported", systemImage: "checkmark.seal")
                    .font(.headline)
            }
        }
    }

    private var checklistSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 8) {
                ForEach(Array(viewModel.bridgeChecklist.enumerated()), id: \.offset) { _, item in
                    Label(item, systemImage: "arrow.turn.down.right")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(4)
        } label: {
            Label("Turn Shorts Viewers Into Subscribers", systemImage: "person.badge.plus")
                .font(.headline)
        }
    }

    private var footer: some View {
        VStack(alignment: .leading, spacing: 6) {
            if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .foregroundStyle(.red)
                    .font(.callout)
            }

            Text(viewModel.statusMessage)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}

#Preview {
    ShortsView()
}
