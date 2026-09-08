"""
Lightweight, non-diagnostic emotion signal analysis for MindCare.

IMPORTANT: This module never produces a mental-health diagnosis. It only
labels general language patterns (e.g. "stress-related language") and
routes distressing messages to a safety/support message. It is not a
substitute for professional care.
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

# Keyword groups used only to describe *language patterns* in the text,
# never to imply a diagnosis.
STRESS_WORDS = [
    "stressed", "pressure", "overwhelmed", "too much", "deadline",
    "exhausted", "burnt out", "burned out", "can't keep up", "no time",
]
SAD_WORDS = [
    "sad", "lonely", "crying", "unhappy", "down", "empty", "hopeless",
    "worthless", "miss", "grief",
]
ANGRY_WORDS = [
    "angry", "furious", "frustrated", "annoyed", "irritated", "mad",
]
ANXIOUS_WORDS = [
    "anxious", "worried", "nervous", "panic", "scared", "afraid",
    "on edge", "restless",
]

# A short list of phrases used only to flag messages for the safety/support
# page. This is a coarse filter, not a clinical assessment.
DISTRESS_PHRASES = [
    "kill myself", "end my life", "want to die", "suicide", "self harm",
    "self-harm", "hurt myself", "no reason to live", "can't go on",
    "better off dead", "ending it all",
]


def _contains_any(text_lower, word_list):
    return any(word in text_lower for word in word_list)


def analyze_text(text):
    """
    Returns a dict with:
      - sentiment: "Positive" | "Neutral" | "Negative"
      - emotion_signal: short descriptive label (never a diagnosis)
      - support_message: general, non-clinical suggestion
      - distress_flag: bool, True if the text matches crisis-related phrasing
    """
    text = (text or "").strip()
    text_lower = text.lower()

    distress_flag = _contains_any(text_lower, DISTRESS_PHRASES)

    if not text:
        return {
            "sentiment": "Neutral",
            "emotion_signal": "No message provided",
            "support_message": (
                "Thanks for checking in. Even a quick mood log helps you "
                "notice patterns over time."
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

    # Determine the most relevant "language pattern" label.
    if distress_flag:
        emotion_signal = "Your message may indicate significant distress"
        support_message = (
            "Your message may indicate that you're going through an "
            "especially difficult moment. Consider contacting a trusted "
            "person or a local emergency/professional support service if "
            "you may be in immediate danger. You can also visit the "
            "Support & Resources page for more options. Please note this "
            "is an automated check and can make mistakes — it is not a "
            "substitute for professional judgment."
        )
    elif _contains_any(text_lower, STRESS_WORDS):
        emotion_signal = "Stress-related language"
        support_message = (
            "It sounds like you're dealing with a lot right now. Try "
            "breaking your work into smaller tasks and taking short "
            "breaks between them."
        )
    elif _contains_any(text_lower, SAD_WORDS):
        emotion_signal = "Sadness-related language"
        support_message = (
            "Feeling this way can be difficult. If possible, consider "
            "reaching out to someone you trust or spending time in an "
            "environment where you feel connected."
        )
    elif _contains_any(text_lower, ANXIOUS_WORDS):
        emotion_signal = "Anxiety-related language"
        support_message = (
            "It sounds like something is weighing on you. Slow, steady "
            "breathing or writing down what's worrying you can sometimes "
            "help create a little distance from it."
        )
    elif _contains_any(text_lower, ANGRY_WORDS):
        emotion_signal = "Frustration/anger-related language"
        support_message = (
            "It's understandable to feel frustrated sometimes. Stepping "
            "away for a few minutes before responding to what's bothering "
            "you may help."
        )
    elif sentiment == "Positive":
        emotion_signal = "Positive language"
        support_message = (
            "It's great that you're having a good moment. Consider noting "
            "what contributed to this feeling so you can revisit it later."
        )
    elif sentiment == "Negative":
        emotion_signal = "General negative sentiment"
        support_message = (
            "Thanks for sharing how you feel. Taking a short pause or "
            "talking with someone you trust may help."
        )
    else:
        emotion_signal = "Neutral sentiment"
        support_message = (
            "Thanks for checking in today. Regularly noting how you feel "
            "can help you spot patterns over time."
        )

    return {
        "sentiment": sentiment,
        "emotion_signal": emotion_signal,
        "support_message": support_message,
        "distress_flag": distress_flag,
    }
