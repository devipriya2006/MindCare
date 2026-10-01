"""
MindCare wellness analysis.

This module combines:
- self-reported mood
- energy
- sleep
- stress
- social connection
- journal sentiment

It produces a general wellness signal.
It does NOT diagnose any mental-health condition.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


MOOD_VALUES = {
    "great": 5,
    "good": 4,
    "okay": 3,
    "low": 2,
    "angry": 2,
    "stressed": 1,
}


MOOD_EMOJI = {
    "great": "😊",
    "good": "🙂",
    "okay": "😐",
    "low": "😔",
    "angry": "😡",
    "stressed": "😰",
}


STRESS_WORDS = [
    "stressed", "pressure", "overwhelmed", "too much",
    "deadline", "exhausted", "burnt out", "burned out",
    "can't keep up", "no time",
]

SAD_WORDS = [
    "sad", "lonely", "crying", "unhappy", "down",
    "empty", "hopeless", "worthless", "miss", "grief",
]

ANGRY_WORDS = [
    "angry", "furious", "frustrated", "annoyed",
    "irritated", "mad",
]

ANXIOUS_WORDS = [
    "anxious", "worried", "nervous", "panic",
    "scared", "afraid", "on edge", "restless",
]


DISTRESS_PHRASES = [
    "kill myself",
    "end my life",
    "want to die",
    "suicide",
    "self harm",
    "self-harm",
    "hurt myself",
    "no reason to live",
    "can't go on",
    "better off dead",
    "ending it all",
]


def _contains_any(text_lower, word_list):
    return any(word in text_lower for word in word_list)


def analyze_text(text):
    """
    Analyze journal text.

    Returns:
        sentiment
        emotion_signal
        support_message
        distress_flag
    """

    text = (text or "").strip()
    text_lower = text.lower()

    distress_flag = _contains_any(
        text_lower,
        DISTRESS_PHRASES
    )

    if not text:
        return {
            "sentiment": "Neutral",
            "emotion_signal": "No message provided",
            "support_message": (
                "Thanks for checking in. Even a quick mood log "
                "helps you notice patterns over time."
            ),
            "distress_flag": False,
        }

    scores = _analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.3:
        sentiment = "Positive"
    elif compound <= -0.3:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    if distress_flag:

        emotion_signal = (
            "Your message may indicate significant distress"
        )

        support_message = (
            "Your message may indicate that you're going through "
            "an especially difficult moment. Consider contacting "
            "a trusted person or a local emergency/professional "
            "support service if you may be in immediate danger."
        )

    elif _contains_any(text_lower, STRESS_WORDS):

        emotion_signal = "Stress-related language"

        support_message = (
            "It sounds like you're dealing with a lot right now. "
            "Try breaking your work into smaller tasks and taking "
            "short breaks between them."
        )

    elif _contains_any(text_lower, SAD_WORDS):

        emotion_signal = "Sadness-related language"

        support_message = (
            "If possible, consider reaching out to someone you "
            "trust or spending time in an environment where you "
            "feel connected."
        )

    elif _contains_any(text_lower, ANXIOUS_WORDS):

        emotion_signal = "Anxiety-related language"

        support_message = (
            "It sounds like something is weighing on you. Slow, "
            "steady breathing or writing down what's worrying "
            "you may help."
        )

    elif _contains_any(text_lower, ANGRY_WORDS):

        emotion_signal = "Frustration/anger-related language"

        support_message = (
            "Stepping away for a few minutes before responding "
            "to what's bothering you may help."
        )

    elif sentiment == "Positive":

        emotion_signal = "Positive language"

        support_message = (
            "It's great that you're having a good moment. "
            "Consider noting what contributed to this feeling."
        )

    elif sentiment == "Negative":

        emotion_signal = "General negative sentiment"

        support_message = (
            "Thanks for sharing how you feel. Taking a short "
            "pause or talking with someone you trust may help."
        )

    else:

        emotion_signal = "Neutral sentiment"

        support_message = (
            "Regularly noting how you feel can help you "
            "spot patterns over time."
        )

    return {
        "sentiment": sentiment,
        "emotion_signal": emotion_signal,
        "support_message": support_message,
        "distress_flag": distress_flag,
    }


def calculate_wellness(
    mood,
    energy,
    sleep,
    stress,
    connection,
    sentiment
):
    """
    Calculate a general wellness signal from the check-in.

    This is NOT a medical or psychological score.
    """

    mood_scores = {
        "great": 100,
        "good": 80,
        "okay": 60,
        "low": 35,
        "angry": 35,
        "stressed": 25,
    }

    energy_scores = {
        "high": 100,
        "moderate": 75,
        "low": 45,
        "very_low": 25,
    }

    sleep_scores = {
        "good": 100,
        "okay": 70,
        "poor": 40,
        "very_poor": 20,
    }

    stress_scores = {
        "low": 100,
        "moderate": 70,
        "high": 40,
        "very_high": 20,
    }

    connection_scores = {
        "connected": 100,
        "somewhat": 70,
        "alone": 40,
        "very_alone": 20,
    }

    sentiment_scores = {
        "Positive": 100,
        "Neutral": 60,
        "Negative": 30,
    }

    mood_score = mood_scores.get(mood, 60)
    energy_score = energy_scores.get(energy, 60)
    sleep_score = sleep_scores.get(sleep, 60)
    stress_score = stress_scores.get(stress, 60)
    connection_score = connection_scores.get(connection, 60)
    text_score = sentiment_scores.get(sentiment, 60)

    overall_score = round(
        (
            mood_score * 0.30
            + energy_score * 0.15
            + sleep_score * 0.15
            + stress_score * 0.20
            + connection_score * 0.10
            + text_score * 0.10
        )
    )

    if overall_score >= 75:
        level = "Positive"

    elif overall_score >= 50:
        level = "Balanced"

    elif overall_score >= 30:
        level = "Needs Attention"

    else:
        level = "Low Wellness Signals"

    # Detect conflicting answers.
    if (
        mood in ["great", "good"]
        and (
            energy in ["low", "very_low"]
            or sleep in ["poor", "very_poor"]
            or stress in ["high", "very_high"]
            or connection in ["alone", "very_alone"]
        )
    ):
        insight = (
            "Your selected mood is positive, but some of your "
            "other responses suggest that you may be dealing "
            "with some challenges today. Your overall check-in "
            "looks more mixed than your mood selection alone."
        )

    elif stress in ["high", "very_high"]:

        insight = (
            "Your responses show elevated stress-related signals. "
            "Consider taking some time to pause, rest, or talk "
            "with someone you trust."
        )

    elif sleep in ["poor", "very_poor"]:

        insight = (
            "Your sleep response stands out in today's check-in. "
            "Rest and maintaining a consistent sleep routine may "
            "be useful to pay attention to."
        )

    elif connection in ["alone", "very_alone"]:

        insight = (
            "You reported feeling less connected today. "
            "Spending time with someone you trust may help you "
            "feel more supported."
        )

    elif energy in ["low", "very_low"]:

        insight = (
            "Your energy appears lower today. Consider giving "
            "yourself some time to rest and avoid putting too "
            "much pressure on yourself."
        )

    else:

        insight = (
            "Your responses appear relatively balanced today. "
            "Keep checking in regularly to notice changes "
            "in your personal patterns."
        )

    return {
        "wellness_score": overall_score,
        "wellness_level": level,
        "wellness_insight": insight,
    }
