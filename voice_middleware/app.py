from flask import Flask, request, jsonify, send_file
from vosk import Model, KaldiRecognizer
from googletrans import Translator
from gtts import gTTS
import os
import wave
import json
import uuid

# -----------------------
# Flask App Setup
# -----------------------
app = Flask(__name__)

# -----------------------
# Load Vosk Model
# -----------------------
model_path = r"D:\Sumit\Chatbot\voice_middleware\vosk-model-small-hi-0.22"

if not os.path.exists(model_path):
    raise FileNotFoundError(f"Vosk model not found at {model_path}")

model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)

# -----------------------
# Routes
# -----------------------

# Homepage
@app.route("/")
def home():
    return "✅ Vosk + Flask + gTTS server is running!"

# Transcribe audio (POST request with file)
@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if "file" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    audio_file = request.files["file"]
    filename = f"temp_{uuid.uuid4().hex}.wav"
    audio_file.save(filename)

    # Open WAV file
    wf = wave.open(filename, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
        return jsonify({"error": "Audio must be WAV mono PCM 16-bit at 16kHz"}), 400

    results = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if recognizer.AcceptWaveform(data):
            results.append(json.loads(recognizer.Result()))

    results.append(json.loads(recognizer.FinalResult()))
    text = " ".join([res.get("text", "") for res in results])

    wf.close()
    os.remove(filename)

    return jsonify({"transcription": text})

# Text to speech
@app.route("/speak", methods=["POST"])
def speak_text():
    data = request.json
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data["text"]
    language = data.get("lang", "hi")  # default Hindi

    # Generate speech
    tts = gTTS(text=text, lang=language)
    filename = f"speech_{uuid.uuid4().hex}.mp3"
    tts.save(filename)

    return send_file(filename, as_attachment=True, download_name="speech.mp3")

# -----------------------
# Run Server
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
