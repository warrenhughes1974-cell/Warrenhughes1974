import SwiftUI

struct BrandThumbnailPreview: View {
    let title: String
    let usePinkTitles: Bool
    let titlePinkRed: Double
    let titlePinkGreen: Double
    let titlePinkBlue: Double

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

            outlinedTitle(title)
                .padding(16)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .frame(height: 140)
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(AppTheme.papaya.opacity(0.35), lineWidth: 1)
        )
    }

    @ViewBuilder
    private func outlinedTitle(_ title: String) -> some View {
        let font = Font.headline.bold()

        ZStack {
            outlineLayer(title, font: font, color: .white, offset: 3.5)
            outlineLayer(title, font: font, color: .black, offset: 2.0)

            Text(title)
                .font(font)
                .foregroundStyle(titleColor)
        }
        .multilineTextAlignment(.leading)
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
        titlePinkBlue: 0.60
    )
    .padding()
    .frame(width: 420)
}
