import Foundation

enum RecommendationEngine {
  // Tune these numbers to make rules stricter or looser.
  private static let minimumDurationSeconds = 8.0
  private static let minimumTalkingPercentForKeep = 40.0
  private static let minimumTalkingPercentForReview = 15.0
  private static let maximumStaticTalkingDurationForKeep = 20.0
  private static let minimumMotionPercentForBRollKeep = 45.0
  private static let longStaticClipReviewThreshold = 90.0

  static func recommend(
    video: VideoFile,
    speech: SpeechAnalysis,
    motion: MotionAnalysis
  ) -> (ClipRecommendation, String) {
    let duration = video.duration

    if duration < minimumDurationSeconds {
      return (.discard, "Too short — under \(Int(minimumDurationSeconds)) seconds.")
    }

    if !speech.hasSpeech && motion.isStatic {
      return (.discard, "Silent and static — dead footage.")
    }

    if speech.hasSpeech && speech.talkingPercent >= minimumTalkingPercentForKeep {
      if motion.isStatic && duration < maximumStaticTalkingDurationForKeep {
        return (.review, "Talking but static — check framing and energy.")
      }

      if motion.isStatic && duration >= longStaticClipReviewThreshold {
        return (.review, "Long static talking clip — may need trimming.")
      }

      if !motion.isStatic && speech.talkingPercent < 60 {
        return (.review, "Talking while moving, but not consistently — verify audio.")
      }

      return (.keep, "Strong talking footage.")
    }

    if !speech.hasSpeech && !motion.isStatic {
      if motion.motionPercent >= minimumMotionPercentForBRollKeep {
        return (.review, "B-roll only — good movement, but no speech.")
      }
      return (.discard, "Weak B-roll — not enough movement or speech.")
    }

    if speech.talkingPercent > 0 && speech.talkingPercent < minimumTalkingPercentForReview {
      return (.discard, "Almost no talking detected.")
    }

    if speech.hasSpeech && speech.talkingPercent < minimumTalkingPercentForKeep {
      return (.review, "Some talking, but below \(Int(minimumTalkingPercentForKeep))% — probably trim or cut.")
    }

    return (.review, "Needs a quick manual look.")
  }
}
