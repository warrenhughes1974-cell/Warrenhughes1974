import Foundation

enum RecommendationEngine {
  static func recommend(
    video: VideoFile,
    speech: SpeechAnalysis,
    motion: MotionAnalysis,
    settings: AnalysisSettingsValues
  ) -> (ClipRecommendation, String) {
    let duration = video.duration

    if duration < settings.minimumDurationSeconds {
      return (.discard, "Too short — under \(Int(settings.minimumDurationSeconds)) seconds.")
    }

    if !speech.hasSpeech && motion.isStatic {
      return (.discard, "Silent and static — dead footage.")
    }

    if speech.hasSpeech && speech.talkingPercent >= settings.minimumTalkingPercentForKeep {
      if motion.isStatic && duration < settings.maximumStaticTalkingDurationForKeep {
        return (.review, "Talking but static — check framing and energy.")
      }

      if motion.isStatic && duration >= settings.longStaticClipReviewThreshold {
        return (.review, "Long static talking clip — may need trimming.")
      }

      if !motion.isStatic && speech.talkingPercent < settings.movingTalkingKeepThreshold {
        return (.review, "Talking while moving, but not consistently — verify audio.")
      }

      return (.keep, "Strong talking footage.")
    }

    if !speech.hasSpeech && !motion.isStatic {
      if motion.motionPercent >= settings.minimumMotionPercentForBRollKeep {
        return (.review, "B-roll only — good movement, but no speech.")
      }
      return (.discard, "Weak B-roll — not enough movement or speech.")
    }

    if speech.talkingPercent > 0 && speech.talkingPercent < settings.minimumTalkingPercentForReview {
      return (.discard, "Almost no talking detected.")
    }

    if speech.hasSpeech && speech.talkingPercent < settings.minimumTalkingPercentForKeep {
      return (.review, "Some talking, but below \(Int(settings.minimumTalkingPercentForKeep))% — probably trim or cut.")
    }

    return (.review, "Needs a quick manual look.")
  }
}
