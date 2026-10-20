
"""
MindCare facial-expression analysis helper.

Expression scores are model estimates, not proof of a person's
actual mood or mental-health condition.
"""

import os
import tempfile

from deepface import DeepFace

ALLOWED_EXPRESSIONS = {
    "angry", "disgust", "fear", "happy",
    "sad", "surprise", "neutral",
}


def analyze_face(image_bytes: bytes) -> dict:
    if not image_bytes:
        raise ValueError("No image was received.")

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".jpg", delete=False
        ) as temp_file:
            temp_file.write(image_bytes)
            temp_path = temp_file.name

        results = DeepFace.analyze(
            img_path=temp_path,
            actions=["emotion"],
            detector_backend="opencv",
            enforce_detection=True,
            silent=True,
        )

        if isinstance(results, list):
            if not results:
                raise ValueError(
                    "No face detected. Keep your face clearly visible."
                )
            result = results[0]
        else:
            result = results

        emotions = result.get("emotion") or {}

        if not emotions:
            raise ValueError("No expression scores were returned.")

        # Keep all seven categories and their model scores.
        scores = {
            name: round(float(emotions.get(name, 0)), 2)
            for name in sorted(ALLOWED_EXPRESSIONS)
        }

        expression = max(scores, key=scores.get)

        return {
            "expression": expression,
            "confidence": scores[expression],
            "scores": scores,
        }

    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(
            "Facial-expression analysis failed. Please try again."
        ) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
