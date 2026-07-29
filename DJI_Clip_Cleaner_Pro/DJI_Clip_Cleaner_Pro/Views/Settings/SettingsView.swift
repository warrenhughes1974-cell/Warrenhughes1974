import SwiftUI

struct SettingsView: View {
    @State private var settings = AnalysisSettings.shared
    @State private var brand = BrandSettings.shared

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                header
                brandSection
                presetsSection
                rulesSection
                footer
            }
            .padding(28)
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Settings")
                .font(.largeTitle.bold())
                .foregroundStyle(AppTheme.carbon)
            Text("Set your brand once, then every title and thumbnail follows the same pattern.")
                .foregroundStyle(.secondary)
        }
    }

    private var brandSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 16) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Series Preset")
                        .fontWeight(.semibold)

                    Picker("Series Preset", selection: $brand.selectedPreset) {
                        ForEach(BrandPreset.allCases) { preset in
                            Text(preset.displayName).tag(preset)
                        }
                    }
                    .pickerStyle(.segmented)
                    .onChange(of: brand.selectedPreset) { _, newValue in
                        if newValue != .custom {
                            brand.seriesName = newValue.seriesName
                        }
                        brand.save()
                    }

                    Text("Pick a preset for consistent hooks, or choose Custom for your own series name.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text("Channel Prefix")
                        .fontWeight(.semibold)
                    TextField("Hughes", text: $brand.channelPrefix)
                        .textFieldStyle(.roundedBorder)
                        .onSubmit { brand.save() }
                    Text("Your channel or creator name at the start of every title.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text("Series Name")
                        .fontWeight(.semibold)
                    TextField("Halloween Store Hunt", text: $brand.seriesName)
                        .textFieldStyle(.roundedBorder)
                        .onSubmit { brand.save() }
                        .disabled(brand.selectedPreset != .custom)
                    Text(
                        brand.selectedPreset == .custom
                            ? "Usually auto-filled from the folder name when you scan a shoot."
                            : "Locked while a preset is selected. Switch to Custom to edit."
                    )
                    .font(.caption)
                    .foregroundStyle(.secondary)
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("Title Format")
                        .fontWeight(.semibold)

                    Picker("Title Format", selection: $brand.titleFormat) {
                        ForEach(BrandTitleFormat.allCases) { format in
                            Text(format.displayName).tag(format)
                        }
                    }
                    .pickerStyle(.menu)
                    .onChange(of: brand.titleFormat) { _, _ in
                        brand.save()
                    }
                }

                Toggle("Use pink titles on thumbnails", isOn: $brand.usePinkTitles)
                    .onChange(of: brand.usePinkTitles) { _, _ in
                        brand.save()
                    }

                VStack(alignment: .leading, spacing: 8) {
                    Text("Thumbnail Preview")
                        .fontWeight(.semibold)

                    BrandThumbnailPreview(
                        title: brand.sampleTitle,
                        usePinkTitles: brand.usePinkTitles,
                        titlePinkRed: brand.titlePinkRed,
                        titlePinkGreen: brand.titlePinkGreen,
                        titlePinkBlue: brand.titlePinkBlue
                    )
                }

                Text("Thumbnails save to a Thumbnails folder as 1280×720 JPEGs with your title along the bottom.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding(4)
            .onChange(of: brand.channelPrefix) { _, _ in brand.save() }
            .onChange(of: brand.seriesName) { _, newValue in
                if brand.selectedPreset == .custom, !newValue.isEmpty {
                    brand.save()
                }
            }
        } label: {
            Label("Brand & Thumbnails", systemImage: "photo.on.rectangle.angled")
                .font(.headline)
                .foregroundStyle(AppTheme.mclarenBlue)
        }
    }

    private var presetsSection: some View {
        GroupBox {
            HStack(spacing: 12) {
                Button("Strict") {
                    settings.applyStrictPreset()
                }
                Button("Balanced") {
                    settings.applyBalancedPreset()
                }
                Button("Lenient") {
                    settings.applyLenientPreset()
                }
                Spacer()
            }
            .padding(4)
        } label: {
            Label("Analysis Presets", systemImage: "slider.horizontal.3")
                .font(.headline)
        }
    }

    private var rulesSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 18) {
                settingSlider(
                    title: "Minimum clip length",
                    value: $settings.minimumDurationSeconds,
                    range: 1...30,
                    step: 1,
                    suffix: "sec",
                    help: "Clips shorter than this are discarded."
                )

                settingSlider(
                    title: "Talking % required for KEEP",
                    value: $settings.minimumTalkingPercentForKeep,
                    range: 5...90,
                    step: 5,
                    suffix: "%",
                    help: "How much talking a clip needs to auto-keep."
                )

                settingSlider(
                    title: "Talking % below = DISCARD",
                    value: $settings.minimumTalkingPercentForReview,
                    range: 1...40,
                    step: 1,
                    suffix: "%",
                    help: "Clips with almost no talking are thrown out."
                )

                settingSlider(
                    title: "Static talking review under",
                    value: $settings.maximumStaticTalkingDurationForKeep,
                    range: 5...60,
                    step: 1,
                    suffix: "sec",
                    help: "Short static talking clips go to REVIEW."
                )

                settingSlider(
                    title: "B-roll motion % for REVIEW",
                    value: $settings.minimumMotionPercentForBRollKeep,
                    range: 10...90,
                    step: 5,
                    suffix: "%",
                    help: "Silent clips need this much motion to avoid discard."
                )

                settingSlider(
                    title: "Long static clip review at",
                    value: $settings.longStaticClipReviewThreshold,
                    range: 30...300,
                    step: 10,
                    suffix: "sec",
                    help: "Very long static talking clips get flagged."
                )

                settingSlider(
                    title: "Moving + talking KEEP threshold",
                    value: $settings.movingTalkingKeepThreshold,
                    range: 20...90,
                    step: 5,
                    suffix: "%",
                    help: "Walking clips need this much talking to auto-keep."
                )
            }
            .padding(4)
        } label: {
            Label("Recommendation Rules", systemImage: "brain.head.profile")
                .font(.headline)
        }
    }

    private var footer: some View {
        Text("Settings save automatically. After changing your brand, use Refresh Titles in Smart Analysis to update every clip.")
            .font(.caption)
            .foregroundStyle(.secondary)
    }

    private func settingSlider(
        title: String,
        value: Binding<Double>,
        range: ClosedRange<Double>,
        step: Double,
        suffix: String,
        help: String
    ) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(title)
                    .fontWeight(.semibold)
                Spacer()
                Text("\(Int(value.wrappedValue)) \(suffix)")
                    .monospacedDigit()
                    .foregroundStyle(.secondary)
            }

            Slider(value: value, in: range, step: step) { editing in
                if !editing {
                    settings.save()
                }
            }

            Text(help)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}

#Preview {
    SettingsView()
}
