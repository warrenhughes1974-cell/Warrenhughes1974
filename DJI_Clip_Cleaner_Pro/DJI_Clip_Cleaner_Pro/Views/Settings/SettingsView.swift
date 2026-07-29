import SwiftUI

struct SettingsView: View {
    @State private var settings = AnalysisSettings.shared

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                header
                presetsSection
                rulesSection
                footer
            }
            .padding(28)
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Garage Setup")
                .font(.largeTitle.bold())
                .foregroundStyle(AppTheme.carbon)
            Text("Tune how Scouting scores your clips. Changes apply the next time you scan a folder.")
                .foregroundStyle(.secondary)
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
            Label("Presets", systemImage: "slider.horizontal.3")
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
        Text("Settings save automatically. Rescan a folder in Scouting to apply new rules.")
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
