import Foundation

enum RecommendationEngine {
  static func recommend(
    video: VideoFile,
    speech: SpeechAnalysis,
    motion: MotionAnalysis
  ) -> (ClipRecommendation, String) {
    let duration = video.duration

    if duration < 3 {
      return (.discard, "Too short to be useful.")
    }

    if !speech.hasSpeech && motion.isStatic {
      return (.discard, "Silent and static — likely dead footage.")
    }

    if speech.hasSpeech && speech.talkingPercent >= 20 {
      if motion.isStatic && duration < 15 {
        return (.review, "Talking, but mostly static — check framing.")
      }
      return (.keep, "Good talking footage.")
    }

    if !speech.hasSpeech && !motion.isStatic {
      return (.review, "B-roll with no speech — inspect manually.")
    }

    if speech.talkingPercent > 0 && speech.talkingPercent < 20 {
      return (.review, "Very little talking detected.")
    }

    return (.review, "Needs a quick manual look.")
  }
}
