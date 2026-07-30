import Foundation

/// Where selected emojis land on the 1280×720 thumbnail.
enum ThumbnailEmojiPosition: String, CaseIterable, Identifiable, Sendable {
    case topRight
    case topLeft
    case bothTop
    case besideTitle

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .topRight:
            return "Top right"
        case .topLeft:
            return "Top left"
        case .bothTop:
            return "Both top corners"
        case .besideTitle:
            return "Beside the title"
        }
    }

    var guidance: String {
        switch self {
        case .topRight:
            return "Classic YouTube placement — big and hard to miss."
        case .topLeft:
            return "Leaves the right side of the frame clear for a face or product."
        case .bothTop:
            return "Puts one emoji in each top corner when you pick two."
        case .besideTitle:
            return "Sits next to the title text along the bottom."
        }
    }
}

/// Curated emoji set for store walks and Halloween hunts. Kept short so the
/// picker stays mouse-friendly instead of dumping the whole Unicode table.
struct ThumbnailEmojiOption: Identifiable, Sendable, Equatable {
    let symbol: String
    let name: String

    var id: String { symbol }

    static let catalog: [ThumbnailEmojiOption] = [
        ThumbnailEmojiOption(symbol: "🎃", name: "Pumpkin"),
        ThumbnailEmojiOption(symbol: "👻", name: "Ghost"),
        ThumbnailEmojiOption(symbol: "🦇", name: "Bat"),
        ThumbnailEmojiOption(symbol: "💀", name: "Skull"),
        ThumbnailEmojiOption(symbol: "🕷️", name: "Spider"),
        ThumbnailEmojiOption(symbol: "🕸️", name: "Web"),
        ThumbnailEmojiOption(symbol: "🧙‍♀️", name: "Witch"),
        ThumbnailEmojiOption(symbol: "😱", name: "Scream"),
        ThumbnailEmojiOption(symbol: "👀", name: "Eyes"),
        ThumbnailEmojiOption(symbol: "🔥", name: "Fire"),
        ThumbnailEmojiOption(symbol: "💥", name: "Boom"),
        ThumbnailEmojiOption(symbol: "😮", name: "Surprised"),
        ThumbnailEmojiOption(symbol: "✨", name: "Sparkles"),
        ThumbnailEmojiOption(symbol: "⭐", name: "Star"),
        ThumbnailEmojiOption(symbol: "❤️", name: "Heart"),
        ThumbnailEmojiOption(symbol: "🛍️", name: "Shopping"),
        ThumbnailEmojiOption(symbol: "🏪", name: "Store"),
        ThumbnailEmojiOption(symbol: "🛒", name: "Cart"),
        ThumbnailEmojiOption(symbol: "🥪", name: "Sandwich"),
        ThumbnailEmojiOption(symbol: "☕", name: "Coffee"),
        ThumbnailEmojiOption(symbol: "📍", name: "Pin"),
        ThumbnailEmojiOption(symbol: "➡️", name: "Arrow"),
        ThumbnailEmojiOption(symbol: "‼️", name: "Exclaim"),
        ThumbnailEmojiOption(symbol: "💯", name: "Hundred")
    ]

    static let maximumSelection = 2
}
