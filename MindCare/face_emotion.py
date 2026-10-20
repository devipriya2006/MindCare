"""
MindCare facial-expression analysis helper.

This module estimates visible facial-expression categories from a captured image.
It does not diagnose mental-health conditions or establish a person's actual mood.
"""

from io import BytesIO
import os
import tempfile

from deepface import DeepFace


ALLOWED_EXPRESSIONS = {
    "angry",
    "disgust",
    "fear",
    "happy",
    "sad",
    "surprise",
    "neutral",
}


def analyze_face(image_bytes: bytes) -> dict:
    """
    Analyze image bytes using DeepFace and return the leading expression.

    Returns:
        {
            "expression": str,
            "confidence": float,
        }

    Raises:
        ValueError: If no usable face/expression is found.
        RuntimeError: If the model cannot analyze the image.
    """
    if not image_bytes:
        raise ValueError("No image was received.")

    temp_path = None
    try:
        # DeepFace accepts a file path. Use a temporary file and remove it
        # immediately after analysis so MindCare does not keep the image.
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
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
                raise ValueError("No face was detected. Try again with your face clearly visible.")
            result = results[0]
        else:
            result = results

        emotions = result.get("emotion") or {}
        if not emotions:
            raise ValueError("The model could not estimate a facial expression.")

        expression = max(emotions, key=emotions.get).lower()
        if expression not in ALLOWED_EXPRESSIONS:
            raise ValueError("The model returned an unsupported expression.")

        # DeepFace returns emotion scores on a 0–100 scale. This is model
        # confidence for its expression classification, not mood certainty.
        confidence = round(float(emotions[expression]), 2)

        return {
            "expression": expression,
            "confidence": confidence,
        }

    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError("Facial-expression analysis failed. Please try again.") from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
