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
            Text(title)
                .font(font)
                .foregroundStyle(.black)
                .offset(x: -2, y: 0)
            Text(title)
                .font(font)
                .foregroundStyle(.black)
                .offset(x: 2, y: 0)
            Text(title)
                .font(font)
                .foregroundStyle(.black)
                .offset(x: 0, y: -2)
            Text(title)
                .font(font)
                .foregroundStyle(.black)
                .offset(x: 0, y: 2)
            Text(title)
                .font(font)
                .foregroundStyle(.black)
                .offset(x: -1.5, y: -1.5)
            Text(title)
                .font(font)
                .foregroundStyle(.black)
                .offset(x: 1.5, y: -1.5)
            Text(title)
                .font(font)
                .foregroundStyle(.black)
                .offset(x: -1.5, y: 1.5)
            Text(title)
                .font(font)
                .foregroundStyle(.black)
                .offset(x: 1.5, y: 1.5)

            Text(title)
                .font(font)
                .foregroundStyle(titleColor)
        }
        .multilineTextAlignment(.leading)
    }
}

struct EditableTitleCell: View {
    let resultID: UUID
    @Bindable var viewModel: AnalysisViewModel

    private var titleBinding: Binding<String> {
        Binding(
            get: {
                viewModel.results.first(where: { $0.id == resultID })?.suggestedTitle ?? ""
            },
            set: { newValue in
                viewModel.updateSuggestedTitle(for: resultID, title: newValue)
            }
        )
    }

    var body: some View {
        TextField("Suggested title", text: titleBinding)
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
