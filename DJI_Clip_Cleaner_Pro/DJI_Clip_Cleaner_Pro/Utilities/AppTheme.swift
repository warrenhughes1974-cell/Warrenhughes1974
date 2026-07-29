import SwiftUI

enum AppTheme {
    static let papaya = Color(
        red: 1.0,
        green: 0.502,
        blue: 0.0
    )

    static let mclarenBlue = Color(
        red: 0.0,
        green: 0.341,
        blue: 0.722
    )

    static let brandPink = Color(
        red: 1.0,
        green: 0.30,
        blue: 0.60
    )

    static let carbon = Color(
        red: 0.07,
        green: 0.08,
        blue: 0.10
    )

    static let softOrange = Color(
        red: 1.0,
        green: 0.502,
        blue: 0.0,
        opacity: 0.14
    )

    static let softBlue = Color(
        red: 0.0,
        green: 0.341,
        blue: 0.722,
        opacity: 0.14
    )

    static var heroGradient: LinearGradient {
        LinearGradient(
            colors: [
                mclarenBlue,
                papaya
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    static var accentGradient: LinearGradient {
        LinearGradient(
            colors: [
                papaya,
                mclarenBlue
            ],
            startPoint: .leading,
            endPoint: .trailing
        )
    }
}
