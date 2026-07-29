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

            Text("Point at your finished Filmora export and generate thumbnail, description, and tags before upload.")
                .foregroundStyle(.secondary)
        }
    }

    private var videoSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 14) {
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

                    Text("Uses your brand settings for channel and series. Type the hook for this upload.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text("YouTube Title")
                        .fontWeight(.semibold)

                    Text(viewModel.titlePreview)
                        .font(.headline)
                        .foregroundStyle(AppTheme.brandPink)
                        .padding(12)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(AppTheme.carbon.opacity(0.92))
                        .clipShape(RoundedRectangle(cornerRadius: 10))
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

                Text("Upload Package creates a YouTube_Prep folder next to your video with thumbnail, title, description, and tags files.")
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

                        Text(viewModel.generatedTags)
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
}

#Preview {
    YouTubePrepView()
}
