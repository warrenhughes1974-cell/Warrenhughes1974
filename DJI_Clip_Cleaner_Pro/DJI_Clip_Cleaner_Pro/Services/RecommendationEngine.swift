import Foundation

enum RecommendationEngine {
  static func recommend(
    video: VideoFile,
    speech: SpeechAnalysis,
    motion: MotionAnalysis,
    settings: AnalysisSettingsValues
  ) -> (ClipRecommendation, String) {
    let duration = video.duration
    let baseRecommendation: (ClipRecommendation, String)

    if duration < settings.minimumDurationSeconds {
      baseRecommendation = (.discard, "Too short — under \(Int(settings.minimumDurationSeconds)) seconds.")
    } else if !speech.hasSpeech && motion.isStatic {
      baseRecommendation = (.discard, "Silent and static — dead footage.")
    } else if speech.hasSpeech && speech.talkingPercent >= settings.minimumTalkingPercentForKeep {
      if motion.isStatic && duration < settings.maximumStaticTalkingDurationForKeep {
        baseRecommendation = (.review, "Talking but static — check framing and energy.")
      } else if motion.isStatic && duration >= settings.longStaticClipReviewThreshold {
        baseRecommendation = (.review, "Long static talking clip — may need trimming.")
      } else if !motion.isStatic && speech.talkingPercent < settings.movingTalkingKeepThreshold {
        baseRecommendation = (.review, "Talking while moving, but not consistently — verify audio.")
      } else {
        baseRecommendation = (.keep, "Strong talking footage.")
      }
    } else if !speech.hasSpeech && !motion.isStatic {
      if motion.motionPercent >= settings.minimumMotionPercentForBRollKeep {
        baseRecommendation = (.bRoll, "B-roll — good movement, no speech (cutaway / scenic).")
      } else {
        baseRecommendation = (.discard, "Weak B-roll — not enough movement or speech.")
      }
    } else if speech.talkingPercent > 0 && speech.talkingPercent < settings.minimumTalkingPercentForReview {
      baseRecommendation = (.discard, "Almost no talking detected.")
    } else if speech.hasSpeech && speech.talkingPercent < settings.minimumTalkingPercentForKeep {
      baseRecommendation = (.review, "Some talking, but below \(Int(settings.minimumTalkingPercentForKeep))% — probably trim or cut.")
    } else {
      baseRecommendation = (.review, "Needs a quick manual look.")
    }

    return applyJerkReview(
      baseRecommendation,
      motion: motion
    )
  }

  private static func applyJerkReview(
    _ recommendation: (ClipRecommendation, String),
    motion: MotionAnalysis
  ) -> (ClipRecommendation, String) {
    guard motion.hasSuddenMovement else {
      return recommendation
    }

    let jerkNote = motion.jerkSummary

    switch recommendation.0 {
    case .keep:
      return (.review, "\(recommendation.1) \(jerkNote).")
    case .bRoll:
      // Jerky cutaways still count as B-roll, but flag for a look.
      return (.bRoll, "\(recommendation.1) \(jerkNote).")
    case .review:
      return (.review, "\(recommendation.1) \(jerkNote).")
    case .discard:
      return recommendation
    default:
      return (.review, jerkNote)
    }
  }
}
