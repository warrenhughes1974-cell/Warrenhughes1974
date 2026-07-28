import Foundation
import Observation

struct AnalysisSettingsValues: Sendable {
    let minimumDurationSeconds: Double
    let minimumTalkingPercentForKeep: Double
    let minimumTalkingPercentForReview: Double
    let maximumStaticTalkingDurationForKeep: Double
    let minimumMotionPercentForBRollKeep: Double
    let longStaticClipReviewThreshold: Double
    let movingTalkingKeepThreshold: Double
}

@MainActor
@Observable
final class AnalysisSettings {
    static let shared = AnalysisSettings()

    private static let storageKey = "DJIClipCleaner.AnalysisSettings"

    var minimumDurationSeconds: Double = 8
    var minimumTalkingPercentForKeep: Double = 40
    var minimumTalkingPercentForReview: Double = 15
    var maximumStaticTalkingDurationForKeep: Double = 20
    var minimumMotionPercentForBRollKeep: Double = 45
    var longStaticClipReviewThreshold: Double = 90
    var movingTalkingKeepThreshold: Double = 60

    private init() {
        load()
    }

    var values: AnalysisSettingsValues {
        AnalysisSettingsValues(
            minimumDurationSeconds: minimumDurationSeconds,
            minimumTalkingPercentForKeep: minimumTalkingPercentForKeep,
            minimumTalkingPercentForReview: minimumTalkingPercentForReview,
            maximumStaticTalkingDurationForKeep: maximumStaticTalkingDurationForKeep,
            minimumMotionPercentForBRollKeep: minimumMotionPercentForBRollKeep,
            longStaticClipReviewThreshold: longStaticClipReviewThreshold,
            movingTalkingKeepThreshold: movingTalkingKeepThreshold
        )
    }

    func save() {
        let payload: [String: Double] = [
            "minimumDurationSeconds": minimumDurationSeconds,
            "minimumTalkingPercentForKeep": minimumTalkingPercentForKeep,
            "minimumTalkingPercentForReview": minimumTalkingPercentForReview,
            "maximumStaticTalkingDurationForKeep": maximumStaticTalkingDurationForKeep,
            "minimumMotionPercentForBRollKeep": minimumMotionPercentForBRollKeep,
            "longStaticClipReviewThreshold": longStaticClipReviewThreshold,
            "movingTalkingKeepThreshold": movingTalkingKeepThreshold
        ]

        UserDefaults.standard.set(payload, forKey: Self.storageKey)
    }

    func load() {
        guard let payload = UserDefaults.standard.dictionary(forKey: Self.storageKey) as? [String: Double] else {
            return
        }

        minimumDurationSeconds = payload["minimumDurationSeconds"] ?? minimumDurationSeconds
        minimumTalkingPercentForKeep = payload["minimumTalkingPercentForKeep"] ?? minimumTalkingPercentForKeep
        minimumTalkingPercentForReview = payload["minimumTalkingPercentForReview"] ?? minimumTalkingPercentForReview
        maximumStaticTalkingDurationForKeep = payload["maximumStaticTalkingDurationForKeep"] ?? maximumStaticTalkingDurationForKeep
        minimumMotionPercentForBRollKeep = payload["minimumMotionPercentForBRollKeep"] ?? minimumMotionPercentForBRollKeep
        longStaticClipReviewThreshold = payload["longStaticClipReviewThreshold"] ?? longStaticClipReviewThreshold
        movingTalkingKeepThreshold = payload["movingTalkingKeepThreshold"] ?? movingTalkingKeepThreshold
    }

    func applyStrictPreset() {
        minimumDurationSeconds = 8
        minimumTalkingPercentForKeep = 40
        minimumTalkingPercentForReview = 15
        maximumStaticTalkingDurationForKeep = 20
        minimumMotionPercentForBRollKeep = 45
        longStaticClipReviewThreshold = 90
        movingTalkingKeepThreshold = 60
        save()
    }

    func applyBalancedPreset() {
        minimumDurationSeconds = 5
        minimumTalkingPercentForKeep = 25
        minimumTalkingPercentForReview = 10
        maximumStaticTalkingDurationForKeep = 15
        minimumMotionPercentForBRollKeep = 30
        longStaticClipReviewThreshold = 120
        movingTalkingKeepThreshold = 40
        save()
    }

    func applyLenientPreset() {
        minimumDurationSeconds = 3
        minimumTalkingPercentForKeep = 15
        minimumTalkingPercentForReview = 5
        maximumStaticTalkingDurationForKeep = 10
        minimumMotionPercentForBRollKeep = 20
        longStaticClipReviewThreshold = 180
        movingTalkingKeepThreshold = 25
        save()
    }
}
