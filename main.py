from flask import Flask, request, jsonify
import os
import requests
import time
import hashlib
import hmac
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)

def verify_slack_request(req):
    timestamp = req.headers.get('X-Slack-Request-Timestamp')
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False

    sig_basestring = f"v0:{timestamp}:{req.get_data(as_text=True)}"
    my_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()

    slack_signature = req.headers.get('X-Slack-Signature')
    return hmac.compare_digest(my_signature, slack_signature)

@app.route("/askai", methods=["POST"])
def ask_ai():
    print("🚀 Received Slack request to /askai")

    user_question = request.form.get("text")
    print(f"📩 User question: {user_question}")

    try:
        print("🌐 Sending request to Groq API...")
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mixtral-8x7b-32768",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Collabor·AI·te, a friendly, smart Slack bot that answers AI/ML questions clearly and supportively."
                    },
                    {
                        "role": "user",
                        "content": user_question
                    }
                ],
                "temperature": 0.7
            }
        )

        print("📦 Raw Response Code:", response.status_code)
        print("📦 Raw Response Text:", response.text)

        try:
            data = response.json()
        except Exception as json_error:
            print("❌ Failed to parse JSON:", response.text)
            raise json_error

        print("✅ Groq API response (parsed):", data)

        if "choices" not in data:
            raise ValueError("Groq response missing 'choices' key")

        answer = data["choices"][0]["message"]["content"]

        print("✅ Answer from Groq:", answer)

        return jsonify({
            "response_type": "in_channel",
            "text": f"🤖 *Collabor·AI·te says:*\n{answer}"
        })

    except Exception as e:
        error_trace = traceback.format_exc()
        print("🛑 Exception caught:", error_trace)
        return jsonify({
            "response_type": "ephemeral",
            "text": f"⚠️ Collabor·AI·te ran into an error: `{str(e)}`"
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)