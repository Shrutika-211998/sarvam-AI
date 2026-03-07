from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

# ==============================
# Load Environment Variables
# ==============================
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SALON_NAME = os.getenv("SALON_NAME", "Beauty & Style Salon")

BASE_URL = "https://api.sarvam.ai"
HEADERS = {
    "api-subscription-key": SARVAM_API_KEY
}

print("\n" + "=" * 50)
print(f"{SALON_NAME} - Voice Assistant Server")
print(f"index.html exists: {os.path.exists(os.path.join(BASE_DIR, 'index.html'))}")
print(f"API Key Loaded: {'YES' if SARVAM_API_KEY else 'NO ❌ Check .env'}")
print("=" * 50 + "\n")


LANG_NAMES = {
    "hi-IN": "Hindi",
    "mr-IN": "Marathi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "kn-IN": "Kannada",
    "gu-IN": "Gujarati",
    "bn-IN": "Bengali",
    "en-IN": "English",
    "en-US": "English"
}

# ==============================
# Serve Frontend
# ==============================
@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')


# ==============================
# Speech To Text
# ==============================
@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():

    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400

    audio_file = request.files['audio']

    try:
        response = requests.post(
            f"{BASE_URL}/speech-to-text",
            headers=HEADERS,
            files={
                'file': (
                    audio_file.filename,
                    audio_file.stream,
                    audio_file.mimetype
                )
            },
            data={
                'model': 'saaras:v3',
                'language_code': 'auto'   # 🔥 IMPORTANT CHANGE
            }
        )

        if response.status_code == 200:
            result = response.json()

            detected_lang = result.get('language_code')

            # 🔥 fallback logic
            if not detected_lang or detected_lang == "unknown":
                detected_lang = "en-IN"

            return jsonify({
                'transcript': result.get('transcript', ''),
                'language_code': detected_lang
            })

        print("STT ERROR:", response.text)
        return jsonify({'error': response.text}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==============================
# Chat API
# ==============================
@app.route('/api/chat', methods=['POST'])
def chat():

    data = request.json
    user_message = data.get('message', '')
    detected_lang = data.get('language_code', 'mr-IN')

    lang_name = LANG_NAMES.get(detected_lang)

    if not lang_name:
         lang_name = "English"

    system_prompt = f"""
You are a helpful assistant for '{SALON_NAME}', an Indian beauty salon.

Services:
Haircut Rs.200
Hair Coloring Rs.800
Facial Rs.500
Threading Rs.50
Pedicure Rs.400
Manicure Rs.300
Head Massage Rs.250
Bridal Makeup Rs.5000

Salon Hours: 9AM–8PM (Mon-Sat)
Location: Near main market.

IMPORTANT:
Reply ONLY in {lang_name}.
Keep response short (2-3 sentences).
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={
                "model": "sarvam-m",
                "messages": messages,
                "temperature": 0.5,
                "max_tokens": 150
            }
        )

        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content']
            return jsonify({
                'reply': reply,
                'language_code': detected_lang
            })

        print("CHAT ERROR:", response.text)
        return jsonify({'error': response.text}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==============================
# Text To Speech
# ==============================
@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():

    data = request.json
    text = data.get('text', '')
    lang = data.get('language_code', 'mr-IN')

    if lang not in LANG_NAMES:
        lang = 'hi-IN'

    try:
        response = requests.post(
            f"{BASE_URL}/text-to-speech",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={
                "inputs": [text[:500]],
                "target_language_code": lang,
                "speaker": "anushka",
                "pitch": 0,
                "pace": 1.0,
                "loudness": 1.5,
                "speech_sample_rate": 22050,
                "enable_preprocessing": True,
                "model": "bulbul:v2"
            }
        )

        if response.status_code == 200:
            audios = response.json().get('audios', [])
            if audios:
                return jsonify({'audio_base64': audios[0]})

        print("TTS ERROR:", response.text)
        return jsonify({'error': response.text}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==============================
# Run Server
# ==============================
if __name__ == '__main__':
    app.run(debug=True, port=5000)