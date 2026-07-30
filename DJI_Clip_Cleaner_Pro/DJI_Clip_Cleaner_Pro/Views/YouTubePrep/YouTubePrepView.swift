import SwiftUI

#if canImport(AppKit)
import AppKit
#endif

struct YouTubePrepView: View {
    @State private var viewModel = YouTubePrepViewModel()
    @State private var brand = BrandSettings.shared

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                header
                videoSection
                thumbnailPicksSection
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

                VStack(alignment: .leading, spacing: 6) {
                    Text("Stores & Places")
                        .fontWeight(.semibold)

                    TextField("HomeGoods, Ross, Ike's Love and Sandwiches", text: $viewModel.placesText)
                        .textFieldStyle(.roundedBorder)

                    Text("Separate with commas. Store names are the most searched part of a store walk, and the mic often misses them.")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Text(viewModel.detectedPlacesSummary)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }

                Toggle("Add channel name to the end of the title", isOn: $viewModel.includeChannelInTitle)
                    .onChange(of: viewModel.includeChannelInTitle) { _, _ in
                        viewModel.refreshTitleVariants()
                    }

                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Title Choices (CTR Ranked)")
                            .fontWeight(.semibold)
                        Spacer()
                        Button("Refresh Titles") {
                            viewModel.refreshTitleVariants()
                        }
                        .buttonStyle(.bordered)
                        .disabled(viewModel.trimmedHook.isEmpty)

                        Button("Copy Selected") {
                            viewModel.copyTitle()
                        }
                        .buttonStyle(.bordered)
                        .disabled(viewModel.generatedTitle.isEmpty)
                    }

                    Text("Ten title options, sorted by projected click-through. Click one to use it.")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    if viewModel.titleVariants.isEmpty {
                        Text(viewModel.generatedTitle.isEmpty ? "Type a hook to build your titles." : viewModel.generatedTitle)
                            .font(.headline)
                            .foregroundStyle(AppTheme.brandPink)
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(AppTheme.carbon.opacity(0.92))
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                    } else {
                        ForEach(Array(viewModel.titleVariants.enumerated()), id: \.element.id) { index, variant in
                            let isSelected = viewModel.selectedTitleID == variant.id
                            Button {
                                viewModel.selectTitle(variant)
                            } label: {
                                HStack(spacing: 12) {
                                    Text(String(format: "%02d", index + 1))
                                        .font(.caption.weight(.bold))
                                        .foregroundStyle(.secondary)
                                        .frame(width: 22)

                                    Text("\(variant.ctrScore)")
                                        .font(.title3.weight(.bold))
                                        .monospacedDigit()
                                        .foregroundStyle(ctrColor(variant.ctrScore))
                                        .frame(width: 36, alignment: .trailing)

                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(variant.title)
                                            .font(.body.weight(isSelected ? .semibold : .regular))
                                            .foregroundStyle(AppTheme.brandPink)
                                            .multilineTextAlignment(.leading)
                                            .frame(maxWidth: .infinity, alignment: .leading)

                                        if !variant.reasons.isEmpty {
                                            Text(variant.reasons.joined(separator: " · "))
                                                .font(.caption2)
                                                .foregroundStyle(.secondary)
                                        }
                                    }

                                    if isSelected {
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundStyle(AppTheme.papaya)
                                    }
                                }
                                .padding(10)
                                .background(
                                    RoundedRectangle(cornerRadius: 10)
                                        .fill(isSelected
                                              ? AppTheme.papaya.opacity(0.18)
                                              : AppTheme.carbon.opacity(0.92))
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }

                    qualityLabel(viewModel.titleQuality)
                }

            }
            .padding(4)
        } label: {
            Label("Finished Video", systemImage: "play.rectangle")
                .font(.headline)
                .foregroundStyle(AppTheme.mclarenBlue)
        }
    }

    private var thumbnailPicksSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 12) {
                    Button("Rank Thumbnails") {
                        viewModel.rankThumbnailOptions()
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(AppTheme.papaya)
                    .disabled(!viewModel.canRankThumbnails)

                    Spacer()
                }

                Text("Scores about 30 frames on faces, sharpness, contrast, and lighting, then shows the strongest picks. Click one to use it.")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                if viewModel.isRankingThumbnails {
                    VStack(alignment: .leading, spacing: 6) {
                        ProgressView(value: viewModel.thumbnailScanProgress)
                            .tint(AppTheme.papaya)
                        Text("Scanning the video. A long export can take a minute.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                if !viewModel.rankedThumbnails.isEmpty {
                    ForEach(viewModel.rankedThumbnails) { option in
                        thumbnailOptionRow(option)
                    }

                    Text("Your pick is saved as the thumbnail in the upload package.")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                } else if viewModel.hasRankedThumbnails, !viewModel.isRankingThumbnails {
                    Label(
                        "No usable frames were found. Try Quick Thumbnail instead.",
                        systemImage: "exclamationmark.triangle.fill"
                    )
                    .font(.caption)
                    .foregroundStyle(.orange)
                } else if !viewModel.isRankingThumbnails {
                    Text(viewModel.canRankThumbnails
                         ? "Click Rank Thumbnails to see your top picks here."
                         : "Choose a video and add thumbnail text to enable ranking.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Divider()

                Text("Brand Preview")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)

                BrandThumbnailPreview(
                    title: viewModel.resolvedThumbnailText,
                    usePinkTitles: brand.usePinkTitles,
                    titlePinkRed: brand.titlePinkRed,
                    titlePinkGreen: brand.titlePinkGreen,
                    titlePinkBlue: brand.titlePinkBlue,
                    titleScale: brand.titleScale
                )

                Text("Change the color and size in Settings → Brand & Thumbnails.")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            .padding(4)
        } label: {
            Label("Thumbnail Picks", systemImage: "photo.stack")
                .font(.headline)
                .foregroundStyle(AppTheme.mclarenBlue)
        }
    }

    private func thumbnailOptionRow(_ option: RankedThumbnailCandidate) -> some View {
        let isSelected = viewModel.selectedThumbnailID == option.id

        return Button {
            viewModel.selectThumbnail(option)
        } label: {
            HStack(spacing: 14) {
                rankedThumbnailImage(path: option.imagePath)

                VStack(alignment: .leading, spacing: 4) {
                    Text(option.rankLabel)
                        .font(.headline)
                        .foregroundStyle(AppTheme.mclarenBlue)

                    Text("\(option.score)")
                        .font(.system(size: 30, weight: .bold, design: .rounded))
                        .monospacedDigit()
                        .foregroundStyle(scoreColor(option.score))

                    Text(option.reasons.joined(separator: " · "))
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Text("Frame at \(option.formattedTime)")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .font(.title2)
                    .foregroundStyle(isSelected ? AppTheme.papaya : .secondary)
            }
            .padding(10)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(isSelected ? AppTheme.papaya.opacity(0.18) : AppTheme.softBlue.opacity(0.5))
            )
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private func rankedThumbnailImage(path: String) -> some View {
        #if canImport(AppKit)
        if let image = NSImage(contentsOfFile: path) {
            Image(nsImage: image)
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(width: 160, height: 90)
                .clipped()
                .clipShape(RoundedRectangle(cornerRadius: 8))
        } else {
            RoundedRectangle(cornerRadius: 8)
                .fill(AppTheme.carbon.opacity(0.6))
                .frame(width: 160, height: 90)
                .overlay {
                    Image(systemName: "photo")
                        .foregroundStyle(.secondary)
                }
        }
        #else
        RoundedRectangle(cornerRadius: 8)
            .fill(AppTheme.carbon.opacity(0.6))
            .frame(width: 160, height: 90)
        #endif
    }

    private func ctrColor(_ score: Int) -> Color {
        if score >= 90 { return AppTheme.papaya }
        if score >= 80 { return AppTheme.mclarenBlue }
        return .secondary
    }

    private func scoreColor(_ score: Int) -> Color {
        if score >= 80 { return AppTheme.papaya }
        if score >= 60 { return AppTheme.mclarenBlue }
        return .secondary
    }

    private var metadataSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 12) {
                    Button("Transcribe Speech") {
                        viewModel.transcribeVideo()
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(AppTheme.papaya)
                    .disabled(!viewModel.canTranscribe)

                    if viewModel.isTranscribing {
                        ProgressView()
                            .controlSize(.small)
                    }

                    Spacer()
                }

                Text(viewModel.transcriptSummary)
                    .font(.caption)
                    .foregroundStyle(.secondary)

                HStack(spacing: 12) {
                    Button("Quick Thumbnail") {
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

                Text("Tip: use Rank Thumbnails above for scored frame picks. Quick Thumbnail grabs one good mid-video frame.")
                    .font(.caption2)
                    .foregroundStyle(.secondary)

                Text("Transcribe once, then Build Upload Package. That saves thumbnail, title, description, tags, captions (.srt), and upload steps in YouTube_Prep/.")
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
