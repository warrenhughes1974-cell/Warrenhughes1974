import Foundation

#if canImport(AppKit)
import AppKit
#endif

/// Fonts available for burned-in thumbnail titles.
enum ThumbnailTitleFont: String, CaseIterable, Identifiable, Sendable {
    case systemBold
    case impact
    case arialBlack
    case avenirHeavy
    case futuraBold
    case helveticaBold
    case georgiaBold

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .systemBold: return "System Bold"
        case .impact: return "Impact"
        case .arialBlack: return "Arial Black"
        case .avenirHeavy: return "Avenir Heavy"
        case .futuraBold: return "Futura Bold"
        case .helveticaBold: return "Helvetica Bold"
        case .georgiaBold: return "Georgia Bold"
        }
    }

    /// macOS PostScript names to try, in preference order.
    var fontNames: [String] {
        switch self {
        case .systemBold:
            return []
        case .impact:
            return ["Impact"]
        case .arialBlack:
            return ["Arial-Black", "Arial Black"]
        case .avenirHeavy:
            return ["AvenirNext-Heavy", "Avenir-Heavy", "Avenir Next Heavy"]
        case .futuraBold:
            return ["Futura-Bold", "Futura-CondensedExtraBold", "Futura Bold"]
        case .helveticaBold:
            return ["Helvetica-Bold", "Helvetica Bold"]
        case .georgiaBold:
            return ["Georgia-Bold", "Georgia Bold"]
        }
    }

    #if canImport(AppKit)
    func nsFont(size: CGFloat) -> NSFont {
        for name in fontNames {
            if let font = NSFont(name: name, size: size) {
                return font
            }
        }
        return NSFont.boldSystemFont(ofSize: size)
    }
    #endif
}
