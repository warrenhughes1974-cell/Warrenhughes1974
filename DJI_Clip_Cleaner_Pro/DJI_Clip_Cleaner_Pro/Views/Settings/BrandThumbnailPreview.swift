import SwiftUI

struct BrandThumbnailPreview: View {
    let title: String
    let usePinkTitles: Bool
    let titlePinkRed: Double
    let titlePinkGreen: Double
    let titlePinkBlue: Double
    var titleScale: Double = 1.0
    var emojis: [String] = []
    var emojiPosition: ThumbnailEmojiPosition = .topRight

    /// Matches the proportions the renderer uses, so the preview tracks what
    /// actually lands in the JPEG rather than being a fixed mock.
    private var fontSize: CGFloat {
        18 * CGFloat(min(max(titleScale, 0.6), 1.6))
    }

    private var emojiSize: CGFloat {
        28 * CGFloat(min(max(titleScale, 0.6), 1.6))
    }

    private var outlineWidth: CGFloat {
        max(fontSize * 0.19, 2.5)
    }

    private var titleColor: Color {
        if usePinkTitles {
            return Color(
                red: titlePinkRed,
                green: titlePinkGreen,
                blue: titlePinkBlue
            )
        }

        return .white
    }

    private var displayTitle: String {
        guard emojiPosition == .besideTitle, !emojis.isEmpty else {
            return title
        }

        return title + " " + emojis.joined(separator: " ")
    }

    var body: some View {
        ZStack(alignment: .bottomLeading) {
            RoundedRectangle(cornerRadius: 10)
                .fill(
                    LinearGradient(
                        colors: [
                            AppTheme.mclarenBlue.opacity(0.55),
                            AppTheme.carbon
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )

            LinearGradient(
                colors: [
                    .clear,
                    AppTheme.carbon.opacity(0.92)
                ],
                startPoint: .center,
                endPoint: .bottom
            )
            .clipShape(RoundedRectangle(cornerRadius: 10))

            outlinedTitle(displayTitle)
                .padding(16)
                .frame(maxWidth: .infinity, alignment: .leading)

            if emojiPosition != .besideTitle {
                cornerEmojis
                    .padding(12)
            }
        }
        .frame(height: 160)
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(AppTheme.papaya.opacity(0.35), lineWidth: 1)
        )
    }

    @ViewBuilder
    private var cornerEmojis: some View {
        switch emojiPosition {
        case .topRight:
            VStack {
                HStack(spacing: 4) {
                    Spacer()
                    ForEach(emojis.reversed(), id: \.self) { emoji in
                        Text(emoji).font(.system(size: emojiSize))
                    }
                }
                Spacer()
            }
        case .topLeft:
            VStack {
                HStack(spacing: 4) {
                    ForEach(emojis, id: \.self) { emoji in
                        Text(emoji).font(.system(size: emojiSize))
                    }
                    Spacer()
                }
                Spacer()
            }
        case .bothTop:
            VStack {
                HStack {
                    if let first = emojis.first {
                        Text(first).font(.system(size: emojiSize))
                    }
                    Spacer()
                    if emojis.count > 1 {
                        Text(emojis[1]).font(.system(size: emojiSize))
                    } else if let first = emojis.first {
                        Text(first).font(.system(size: emojiSize))
                    }
                }
                Spacer()
            }
        case .besideTitle:
            EmptyView()
        }
    }

    @ViewBuilder
    private func outlinedTitle(_ title: String) -> some View {
        let font = Font.system(size: fontSize, weight: .heavy)

        ZStack {
            outlineLayer(title, font: font, color: .white, offset: outlineWidth)
            outlineLayer(title, font: font, color: .black, offset: outlineWidth * 0.57)

            Text(title)
                .font(font)
                .foregroundStyle(titleColor)
        }
        .multilineTextAlignment(.leading)
        .lineLimit(3)
    }

    @ViewBuilder
    private func outlineLayer(
        _ title: String,
        font: Font,
        color: Color,
        offset: CGFloat
    ) -> some View {
        Text(title)
            .font(font)
            .foregroundStyle(color)
            .offset(x: -offset, y: 0)
        Text(title)
            .font(font)
            .foregroundStyle(color)
            .offset(x: offset, y: 0)
        Text(title)
            .font(font)
            .foregroundStyle(color)
            .offset(x: 0, y: -offset)
        Text(title)
            .font(font)
            .foregroundStyle(color)
            .offset(x: 0, y: offset)
        Text(title)
            .font(font)
            .foregroundStyle(color)
            .offset(x: -offset * 0.75, y: -offset * 0.75)
        Text(title)
            .font(font)
            .foregroundStyle(color)
            .offset(x: offset * 0.75, y: -offset * 0.75)
        Text(title)
            .font(font)
            .foregroundStyle(color)
            .offset(x: -offset * 0.75, y: offset * 0.75)
        Text(title)
            .font(font)
            .foregroundStyle(color)
            .offset(x: offset * 0.75, y: offset * 0.75)
    }
}

struct EditableHookCell: View {
    let resultID: UUID
    @Bindable var viewModel: AnalysisViewModel

    private var hookBinding: Binding<String> {
        Binding(
            get: {
                viewModel.results.first(where: { $0.id == resultID })?.suggestedHook ?? ""
            },
            set: { newValue in
                viewModel.updateSuggestedHook(for: resultID, hook: newValue)
            }
        )
    }

    var body: some View {
        TextField("Type hook", text: hookBinding)
            .textFieldStyle(.plain)
            .font(.caption)
            .foregroundStyle(AppTheme.brandPink)
            .lineLimit(2)
    }
}

#Preview {
    BrandThumbnailPreview(
        title: "Hughes · Halloween Hunt · Creepy Aisle Find",
        usePinkTitles: true,
        titlePinkRed: 1.0,
        titlePinkGreen: 0.30,
        titlePinkBlue: 0.60,
        titleScale: 1.0,
        emojis: ["🎃", "👻"],
        emojiPosition: .topRight
    )
    .padding()
    .frame(width: 420)
}
