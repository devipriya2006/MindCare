/* MindCare webcam capture and facial-expression request.
   The Flask endpoint /api/analyze-face will be added when we update app.py. */

(() => {
  const video = document.getElementById("webcam");
  const canvas = document.getElementById("capture-canvas");
  const startButton = document.getElementById("start-camera");
  const captureButton = document.getElementById("capture-face");
  const stopButton = document.getElementById("stop-camera");
  const statusBox = document.getElementById("face-status");
  const resultBox = document.getElementById("face-result");
  const expressionField = document.getElementById("detected-expression");
  const confidenceField = document.getElementById("expression-confidence");
  const confirmButton = document.getElementById("confirm-expression");
  const correctionSelect = document.getElementById("corrected-expression");

  if (!video || !canvas || !startButton || !captureButton) return;

  let stream = null;
  let detectedExpression = "";

  function setStatus(message, isError = false) {
    statusBox.textContent = message;
    statusBox.setAttribute("aria-live", "polite");
    statusBox.dataset.state = isError ? "error" : "normal";
  }

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    video.srcObject = null;
    startButton.disabled = false;
    captureButton.disabled = true;
    stopButton.disabled = true;
  }

  startButton.addEventListener("click", async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("Your browser does not support webcam access. Use a recent browser over HTTPS or localhost.", true);
      return;
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
        audio: false
      });
      video.srcObject = stream;
      await video.play();
      startButton.disabled = true;
      captureButton.disabled = false;
      stopButton.disabled = false;
      resultBox.hidden = true;
      setStatus("Camera is ready. Position your face clearly in the frame.");
    } catch (error) {
      setStatus("Camera permission was not granted or the camera is unavailable.", true);
    }
  });

  stopButton.addEventListener("click", () => {
    stopCamera();
    setStatus("Camera stopped.");
  });

  captureButton.addEventListener("click", async () => {
    if (!stream || !video.videoWidth || !video.videoHeight) {
      setStatus("Start the camera and wait until the video appears.", true);
      return;
    }

    captureButton.disabled = true;
    setStatus("Analyzing facial expression…");

    try {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const context = canvas.getContext("2d");
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      const blob = await new Promise((resolve, reject) => {
        canvas.toBlob((value) => value ? resolve(value) : reject(new Error("Image capture failed.")), "image/jpeg", 0.85);
      });

      const formData = new FormData();
      formData.append("image", blob, "capture.jpg");

      const response = await fetch("/api/analyze-face", {
        method: "POST",
        body: formData,
        headers: { "X-Requested-With": "XMLHttpRequest" }
      });

      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.error || "Could not analyze the image. Please try again.");
      }

      detectedExpression = String(data.expression || "").toLowerCase();
      if (!detectedExpression) throw new Error("The server returned no expression.");

      expressionField.textContent = detectedExpression.charAt(0).toUpperCase() + detectedExpression.slice(1);
      confidenceField.textContent = `${Number(data.confidence).toFixed(1)}% model confidence`;
      if (correctionSelect) correctionSelect.value = detectedExpression;
      resultBox.hidden = false;
      setStatus("Estimate ready. Please confirm or correct it before saving.");
    } catch (error) {
      setStatus(error.message || "Something went wrong. Please try again.", true);
    } finally {
      captureButton.disabled = !stream;
    }
  });

  if (confirmButton) {
    confirmButton.addEventListener("click", () => {
      const confirmed = correctionSelect ? correctionSelect.value : detectedExpression;
      if (!detectedExpression || !confirmed) {
        setStatus("Capture an expression before confirming.", true);
        return;
      }

      // The save endpoint will be connected when app.py is updated.
      const form = document.getElementById("confirm-expression-form");
      const detectedInput = document.getElementById("detected-expression-input");
      const confidenceInput = document.getElementById("expression-confidence-input");
      const confirmedInput = document.getElementById("confirmed-expression-input");

      if (!form || !detectedInput || !confidenceInput || !confirmedInput) {
        setStatus("The save form is not connected yet. We'll connect it when updating app.py.", true);
        return;
      }

      detectedInput.value = detectedExpression;
      confidenceInput.value = confidenceField.textContent.replace("% model confidence", "").trim();
      confirmedInput.value = confirmed;
      form.requestSubmit();
    });
  }

  window.addEventListener("pagehide", stopCamera);
})();
