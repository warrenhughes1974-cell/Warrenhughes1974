import SwiftUI

struct YouTubePrepView: View {
    @State private var viewModel = YouTubePrepViewModel()
    @State private var brand = BrandSettings.shared

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                header
                videoSection
                metadataSection
                outputSection
                footer
            }
            .padding(24)
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 10) {
                Text("YouTube Prep")
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

            Text("Point at your finished Filmora export and build a search-optimized title, thumbnail, description, and tags.")
                .foregroundStyle(.secondary)
        }
    }

    private var videoSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 16) {
                HStack(spacing: 12) {
                    Button("Choose Video…") {
                        viewModel.chooseVideo()
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(AppTheme.papaya)

                    if viewModel.isWorking {
                        ProgressView()
                            .controlSize(.small)
                    }

                    Spacer()
                }

                if let videoURL = viewModel.selectedVideoURL {
                    Text(videoURL.path)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                        .truncationMode(.middle)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text("Hook")
                        .fontWeight(.semibold)

                    TextField("Creepy Aisle Find", text: $viewModel.hook)
                        .textFieldStyle(.roundedBorder)
                        .onChange(of: viewModel.hook) { _, _ in
                            viewModel.hookDidChange()
                        }

                    Text("What this video is actually about. This drives your title, thumbnail, and tags.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text("Thumbnail Text")
                        .fontWeight(.semibold)

                    TextField("CREEPY AISLE FIND", text: $viewModel.thumbnailText)
                        .textFieldStyle(.roundedBorder)
                        .onChange(of: viewModel.thumbnailText) { _, _ in
                            viewModel.thumbnailTextDidChange()
                        }

                    qualityLabel(viewModel.thumbnailTextQuality)

                    Text("Keep it to 3 or 4 words. Thumbnail text should add to the title, not repeat it.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Toggle("Add channel name to the end of the title", isOn: $viewModel.includeChannelInTitle)

                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("YouTube Title")
                            .fontWeight(.semibold)
                        Spacer()
                        Button("Copy") {
                            viewModel.copyTitle()
                        }
                        .buttonStyle(.bordered)
                        .disabled(!viewModel.canGenerate)
                    }

                    Text(viewModel.generatedTitle.isEmpty ? "Type a hook to build your title." : viewModel.generatedTitle)
                        .font(.headline)
                        .foregroundStyle(AppTheme.brandPink)
                        .padding(12)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(AppTheme.carbon.opacity(0.92))
                        .clipShape(RoundedRectangle(cornerRadius: 10))

                    qualityLabel(viewModel.titleQuality)
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("Thumbnail Preview")
                        .fontWeight(.semibold)

                    BrandThumbnailPreview(
                        title: viewModel.resolvedThumbnailText,
                        usePinkTitles: brand.usePinkTitles,
                        titlePinkRed: brand.titlePinkRed,
                        titlePinkGreen: brand.titlePinkGreen,
                        titlePinkBlue: brand.titlePinkBlue
                    )
                }
            }
            .padding(4)
        } label: {
            Label("Finished Video", systemImage: "play.rectangle")
                .font(.headline)
                .foregroundStyle(AppTheme.mclarenBlue)
        }
    }

    private var metadataSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 12) {
                    Button("Generate Thumbnail") {
                        viewModel.generateThumbnail()
                    }
                    .buttonStyle(.bordered)
                    .disabled(!viewModel.canGenerate || viewModel.isWorking)

                    Button("Generate Description") {
                        viewModel.generateDescription()
                    }
                    .buttonStyle(.bordered)
                    .disabled(!viewModel.canGenerate)

                    Button("Generate Tags") {
                        viewModel.generateTags()
                    }
                    .buttonStyle(.bordered)
                    .disabled(!viewModel.canGenerate)

                    Button("Build Upload Package") {
                        viewModel.generateUploadPackage()
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(AppTheme.mclarenBlue)
                    .disabled(!viewModel.canGenerate || viewModel.isWorking)
                }

                Text("Upload Package writes the thumbnail, title, description, tags, and step-by-step notes into a YouTube_Prep folder next to your video.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding(4)
        } label: {
            Label("Generate", systemImage: "sparkles")
                .font(.headline)
        }
    }

    private var outputSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 16) {
                if !viewModel.generatedDescription.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Description")
                                .fontWeight(.semibold)
                            Spacer()
                            Button("Copy") {
                                viewModel.copyDescription()
                            }
                            .buttonStyle(.bordered)
                        }

                        qualityLabel(viewModel.descriptionQuality)

                        Text(viewModel.generatedDescription)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .textSelection(.enabled)
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(AppTheme.softBlue)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                    }
                }

                if !viewModel.generatedTags.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Tags")
                                .fontWeight(.semibold)
                            Spacer()
                            Button("Copy") {
                                viewModel.copyTags()
                            }
                            .buttonStyle(.bordered)
                        }

                        qualityLabel(viewModel.tagsQuality)

                        Text(viewModel.tagsLine)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .textSelection(.enabled)
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(AppTheme.softOrange)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                    }
                }

                if !viewModel.thumbnailPath.isEmpty {
                    Text("Thumbnail: \(viewModel.thumbnailPath)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                        .truncationMode(.middle)
                }

                if viewModel.generatedDescription.isEmpty && viewModel.generatedTags.isEmpty {
                    Text("Generate a description and tags, or click Build Upload Package to create everything at once.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(4)
        } label: {
            Label("Ready For YouTube", systemImage: "square.and.arrow.up")
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

    private func qualityLabel(_ quality: MetadataQuality) -> some View {
        Label(quality.message, systemImage: qualityIcon(quality.level))
            .font(.caption)
            .foregroundStyle(qualityColor(quality.level))
    }

    private func qualityIcon(_ level: MetadataQualityLevel) -> String {
        switch level {
        case .good:
            return "checkmark.circle.fill"
        case .warning:
            return "exclamationmark.triangle.fill"
        case .problem:
            return "xmark.circle.fill"
        }
    }

    private func qualityColor(_ level: MetadataQualityLevel) -> Color {
        switch level {
        case .good:
            return .green
        case .warning:
            return .orange
        case .problem:
            return .red
        }
    }
}

#Preview {
    YouTubePrepView()
}
