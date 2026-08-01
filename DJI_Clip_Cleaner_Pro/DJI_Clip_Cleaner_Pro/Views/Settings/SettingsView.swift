import SwiftUI

#if canImport(AppKit)
import AppKit
#endif

struct SettingsView: View {
    @State private var settings = AnalysisSettings.shared
    @State private var brand = BrandSettings.shared
    @State private var openAI = OpenAISettings.shared
    @State private var openAIKeyMessage: String?

    /// Bridges the stored RGB components to the system color picker.
    private var titleColorBinding: Binding<Color> {
        Binding(
            get: {
                Color(
                    red: brand.titlePinkRed,
                    green: brand.titlePinkGreen,
                    blue: brand.titlePinkBlue
                )
            },
            set: { newValue in
                #if canImport(AppKit)
                guard let resolved = NSColor(newValue).usingColorSpace(.sRGB) else { return }
                brand.titlePinkRed = Double(resolved.redComponent)
                brand.titlePinkGreen = Double(resolved.greenComponent)
                brand.titlePinkBlue = Double(resolved.blueComponent)
                brand.save()
                #endif
            }
        )
    }

    private func isActiveSwatch(_ swatch: ThumbnailColorSwatch) -> Bool {
        let tolerance = 0.02
        return abs(brand.titlePinkRed - swatch.red) < tolerance
            && abs(brand.titlePinkGreen - swatch.green) < tolerance
            && abs(brand.titlePinkBlue - swatch.blue) < tolerance
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                header
                openAISection
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

    private var openAISection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 14) {
                Text("Pick OpenAI or Google Gemini, paste that provider’s API key, then turn on the cloud features you want.")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                VStack(alignment: .leading, spacing: 6) {
                    Text("Provider")
                        .fontWeight(.semibold)
                    Picker("Provider", selection: $openAI.provider) {
                        ForEach(CloudAIProvider.allCases) { provider in
                            Text(provider.displayName).tag(provider)
                        }
                    }
                    .pickerStyle(.segmented)
                    .onChange(of: openAI.provider) { _, _ in
                        openAI.apiKeyDraft = ""
                        openAI.save()
                    }
                }

                Text(openAI.apiKeyPreview)
                    .font(.caption.monospaced())
                    .foregroundStyle(openAI.hasAPIKey ? AppTheme.mclarenBlue : .secondary)

                SecureField(
                    openAI.provider == .openAI ? "sk-..." : "AIza... (Gemini API key)",
                    text: $openAI.apiKeyDraft
                )
                .textFieldStyle(.roundedBorder)

                HStack(spacing: 10) {
                    Button("Save API Key") {
                        if openAI.saveAPIKeyFromDraft() {
                            openAIKeyMessage = "\(openAI.provider.displayName) key saved on this Mac."
                        } else if openAI.provider == .openAI {
                            openAIKeyMessage = "OpenAI key should start with sk- and look like a real secret key."
                        } else {
                            openAIKeyMessage = "Paste a full Gemini API key from Google AI Studio (usually starts with AIza)."
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(AppTheme.papaya)

                    Button("Clear Key") {
                        openAI.clearAPIKey()
                        openAIKeyMessage = "\(openAI.provider.displayName) key removed."
                    }
                    .buttonStyle(.bordered)
                    .disabled(!openAI.hasAPIKey)
                }

                if let openAIKeyMessage {
                    Text(openAIKeyMessage)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Toggle("Use cloud transcription", isOn: $openAI.useWhisper)
                    .onChange(of: openAI.useWhisper) { _, _ in openAI.save() }
                Toggle("Use cloud Story Review draft", isOn: $openAI.useCloudStory)
                    .onChange(of: openAI.useCloudStory) { _, _ in openAI.save() }
                Toggle("Use cloud description / tags / title polish", isOn: $openAI.useCloudCopy)
                    .onChange(of: openAI.useCloudCopy) { _, _ in openAI.save() }
                Toggle("Use cloud Vision for thumbnail picks + overlay text", isOn: $openAI.useVisionThumbnails)
                    .onChange(of: openAI.useVisionThumbnails) { _, _ in openAI.save() }
                Toggle("Use cloud AI Assist on Smart Analysis (demote junk / confirm labels)", isOn: $openAI.useAIAssistAnalysis)
                    .onChange(of: openAI.useAIAssistAnalysis) { _, _ in openAI.save() }
                Toggle("Use cloud cut hints on Smart Analysis (KEEP/CUT time ranges)", isOn: $openAI.useAICutHints)
                    .onChange(of: openAI.useAICutHints) { _, _ in openAI.save() }
                Toggle("Use cloud Shorts refine (reorder moments + polish titles)", isOn: $openAI.useCloudShortsRefine)
                    .onChange(of: openAI.useCloudShortsRefine) { _, _ in openAI.save() }

                VStack(alignment: .leading, spacing: 6) {
                    Text("Model")
                        .fontWeight(.semibold)
                    if openAI.provider == .openAI {
                        Picker("Chat model", selection: $openAI.model) {
                            Text("gpt-4o-mini (cheaper)").tag("gpt-4o-mini")
                            Text("gpt-4o (stronger)").tag("gpt-4o")
                        }
                        .pickerStyle(.segmented)
                        .onChange(of: openAI.model) { _, _ in openAI.save() }
                    } else {
                        Picker("Gemini model", selection: $openAI.geminiModel) {
                            Text("gemini-3-flash-preview (matches AI Studio)").tag("gemini-3-flash-preview")
                            Text("gemini-2.5-flash (fast)").tag("gemini-2.5-flash")
                            Text("gemini-2.5-pro (stronger)").tag("gemini-2.5-pro")
                        }
                        .pickerStyle(.menu)
                        .onChange(of: openAI.geminiModel) { _, _ in openAI.save() }
                    }
                }

                if openAI.provider == .openAI {
                    Link(
                        "Get an OpenAI key at platform.openai.com/api-keys",
                        destination: URL(string: "https://platform.openai.com/api-keys")!
                    )
                    .font(.caption)
                } else {
                    Link(
                        "Get a Gemini key at aistudio.google.com/apikey",
                        destination: URL(string: "https://aistudio.google.com/apikey")!
                    )
                    .font(.caption)
                }

                Text("Only the selected provider is used. Transcripts, story text, thumbnail frames, cut-hint audio, and Shorts titles are sent when those toggles are on. Gemini often has a generous free daily quota; OpenAI is pay-as-you-go. AI Assist never upgrades weak clips to KEEP. Shorts refine never changes cut times.")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            .padding(4)
        } label: {
            Label("Cloud AI (OpenAI or Gemini)", systemImage: "cloud.fill")
                .font(.headline)
                .foregroundStyle(AppTheme.mclarenBlue)
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
                    .pickerStyle(.menu)
                    .frame(maxWidth: 320, alignment: .leading)
                    .onChange(of: brand.selectedPreset) { _, newValue in
                        if newValue != .custom {
                            brand.seriesName = newValue.seriesName
                        }
                        brand.save()
                    }

                    Text("Dropdown of lifestyle series labels (travel, food, parks, shopping, etc.). Pick the series this shoot belongs to — or Custom for your own name. Episode facts still come from Story Review.")
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
                    Text("Channel Context — People, Pets & Name Corrections")
                        .fontWeight(.semibold)
                    TextEditor(text: $brand.channelContext)
                        .frame(minHeight: 90)
                        .padding(6)
                        .background(AppTheme.softBlue)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                        .onChange(of: brand.channelContext) { _, _ in
                            brand.save()
                        }
                    Text("Used only by Apple Intelligence on this Mac for identity and spelling (for example “Coco is a dog”, “Brianna”). It never proves who is in the video. Prefer a short name list over “family channel” wording so the model does not invent lifestyle themes.")
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

                VStack(alignment: .leading, spacing: 6) {
                    Text("Default Hook")
                        .fontWeight(.semibold)
                    TextField("Creepy Aisle Find", text: $brand.defaultHook)
                        .textFieldStyle(.roundedBorder)
                        .onSubmit { brand.save() }
                    Text("Optional preview hook for Settings. Each clip gets its own editable Hook in Smart Analysis.")
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

                VStack(alignment: .leading, spacing: 10) {
                    Text("Thumbnail Font")
                        .fontWeight(.semibold)

                    Picker("Thumbnail Font", selection: $brand.titleFont) {
                        ForEach(ThumbnailTitleFont.allCases) { font in
                            Text(font.displayName).tag(font)
                        }
                    }
                    .pickerStyle(.menu)
                    .onChange(of: brand.titleFont) { _, _ in
                        brand.save()
                    }

                    Text("Used for burned-in thumbnail titles (Impact is the classic YouTube look).")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                VStack(alignment: .leading, spacing: 10) {
                    Text("Thumbnail Text Color")
                        .fontWeight(.semibold)

                    Toggle("Use a custom color", isOn: $brand.usePinkTitles)
                        .onChange(of: brand.usePinkTitles) { _, _ in
                            brand.save()
                        }

                    if brand.usePinkTitles {
                        ColorPicker(
                            "Pick any color",
                            selection: titleColorBinding,
                            supportsOpacity: false
                        )

                        HStack(spacing: 8) {
                            ForEach(ThumbnailColorSwatch.all) { swatch in
                                Button {
                                    brand.applyColorSwatch(swatch)
                                } label: {
                                    Circle()
                                        .fill(Color(red: swatch.red, green: swatch.green, blue: swatch.blue))
                                        .frame(width: 26, height: 26)
                                        .overlay(
                                            Circle().stroke(
                                                isActiveSwatch(swatch) ? AppTheme.papaya : Color.secondary.opacity(0.4),
                                                lineWidth: isActiveSwatch(swatch) ? 3 : 1
                                            )
                                        )
                                }
                                .buttonStyle(.plain)
                                .help(swatch.name)
                            }

                            Spacer()
                        }
                    }

                    Toggle("Thick black + white text outline", isOn: $brand.useTextOutline)
                        .onChange(of: brand.useTextOutline) { _, _ in
                            brand.save()
                        }

                    Text(brand.useTextOutline
                         ? "Fill uses your color above. Outline is a thick black outer ring with a white inner ring."
                         : "Outline off: soft black shadow over the dark fade only.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Thumbnail Text Size")
                            .fontWeight(.semibold)
                        Spacer()
                        Text("\(Int(brand.titleScale * 100))%")
                            .font(.caption)
                            .monospacedDigit()
                            .foregroundStyle(.secondary)
                    }

                    Slider(
                        value: $brand.titleScale,
                        in: BrandSettings.minimumTitleScale...BrandSettings.maximumTitleScale,
                        step: 0.05
                    ) { editing in
                        if !editing {
                            brand.save()
                        }
                    }

                    HStack {
                        Button("Reset to 100%") {
                            brand.titleScale = 1.0
                            brand.save()
                        }
                        .buttonStyle(.bordered)
                        .disabled(abs(brand.titleScale - 1.0) < 0.001)

                        Spacer()
                    }

                    Text("100% is the size the app picks on its own. Long titles still shrink to fit, so this raises the ceiling rather than forcing one size.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                VStack(alignment: .leading, spacing: 10) {
                    HStack {
                        Text("Thumbnail Emoticons")
                            .fontWeight(.semibold)
                        Spacer()
                        if !brand.thumbnailEmojis.isEmpty {
                            Text(brand.thumbnailEmojis.joined(separator: " "))
                                .font(.title3)
                        }
                    }

                    Text("Pick up to \(ThumbnailEmojiOption.maximumSelection). Click again to remove. A third click replaces the oldest pick.")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    LazyVGrid(
                        columns: Array(repeating: GridItem(.flexible(), spacing: 8), count: 8),
                        spacing: 8
                    ) {
                        ForEach(ThumbnailEmojiOption.catalog) { option in
                            let isSelected = brand.thumbnailEmojis.contains(option.symbol)

                            Button {
                                brand.toggleThumbnailEmoji(option.symbol)
                            } label: {
                                Text(option.symbol)
                                    .font(.system(size: 26))
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 8)
                                    .background(
                                        RoundedRectangle(cornerRadius: 8)
                                            .fill(isSelected
                                                  ? AppTheme.papaya.opacity(0.22)
                                                  : AppTheme.softBlue.opacity(0.55))
                                    )
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 8)
                                            .stroke(
                                                isSelected ? AppTheme.papaya : Color.clear,
                                                lineWidth: 2
                                            )
                                    )
                            }
                            .buttonStyle(.plain)
                            .help(option.name)
                        }
                    }

                    HStack {
                        Picker("Placement", selection: $brand.emojiPosition) {
                            ForEach(ThumbnailEmojiPosition.allCases) { position in
                                Text(position.displayName).tag(position)
                            }
                        }
                        .pickerStyle(.menu)
                        .onChange(of: brand.emojiPosition) { _, _ in
                            brand.save()
                        }

                        Button("Clear") {
                            brand.clearThumbnailEmojis()
                        }
                        .buttonStyle(.bordered)
                        .disabled(brand.thumbnailEmojis.isEmpty)

                        Spacer()
                    }

                    Text(brand.emojiPosition.guidance)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("Thumbnail Preview")
                        .fontWeight(.semibold)

                    BrandThumbnailPreview(
                        title: brand.sampleTitle,
                        usePinkTitles: brand.usePinkTitles,
                        titlePinkRed: brand.titlePinkRed,
                        titlePinkGreen: brand.titlePinkGreen,
                        titlePinkBlue: brand.titlePinkBlue,
                        titleScale: brand.titleScale,
                        emojis: brand.thumbnailEmojis,
                        emojiPosition: brand.emojiPosition,
                        titleFont: brand.titleFont,
                        useTextOutline: brand.useTextOutline
                    )
                }

                Text("Thumbnails save to a Thumbnails folder as 1280×720 JPEGs with your title along the bottom.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding(4)
            .onChange(of: brand.channelPrefix) { _, _ in brand.save() }
            .onChange(of: brand.defaultHook) { _, _ in brand.save() }
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
                    title: "B-roll motion % for B-ROLL",
                    value: $settings.minimumMotionPercentForBRollKeep,
                    range: 10...90,
                    step: 5,
                    suffix: "%",
                    help: "Silent clips with this much motion are labeled B-ROLL."
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
