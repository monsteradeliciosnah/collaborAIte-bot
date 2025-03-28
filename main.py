from flask import Flask, request, jsonify
import os
import requests
import hashlib
import hmac
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)

# Slack signature verification
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

# Slack AI command handler
@app.route("/askai", methods=["POST"])
def ask_ai():
    user_question = request.form.get("text")
    user_id = request.form.get("user_id")

    print(f"📩 User question: {user_question}")
    print("🌐 Sending request to Groq API...")

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are Collabor·AI·te, a friendly, smart AI Slack assistant that answers AI/ML questions clearly and with encouragement."},
                    {"role": "user", "content": user_question}
                ],
                "temperature": 0.7
            }
        )

        print(f"📦 Raw Response Code: {response.status_code}")
        print(f"📦 Raw Response Text: {response.text}")

        data = response.json()
        if "choices" not in data:
            raise ValueError("Groq response missing 'choices' key")

        answer = data["choices"][0]["message"]["content"]
        return jsonify({
            "response_type": "in_channel",
            "text": f"🤖 *Collabor·AI·te says:*\n{answer}"
        })

    except Exception as e:
        print(f"🛑 Exception caught: {e}")
        return jsonify({
            "response_type": "ephemeral",
            "text": f"⚠️ Collabor·AI·te ran into an error: {e}"
        })

# Welcome new users
@app.route("/welcome", methods=["POST"])
def welcome_new_user():
    data = request.json
    event = data.get("event", {})

    user_id = event.get("user", {}).get("id")
    if not user_id:
        return "No user ID found", 400

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    # DM to user
    dm_payload = {
        "channel": user_id,
        "text": (
            f"👋 Welcome to [collabor·AI·te], <@{user_id}>!\n\n"
            "We’re so happy you joined 💜\n\n"
            "🚀 Here's your onboarding form: https://forms.gle/MD2rGNS3Mq83oREh7\n"
            "💡 Ask AI/ML questions using the `/askai` command\n"
            "🔥 And don't forget to drop your AI-interest heat level!"
        )
    }
    requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=dm_payload)

    # Public welcome in general
    general_payload = {
        "channel": "#general",
        "text": f"🎉 Let’s welcome <@{user_id}> to [collabor·AI·te]! Say hi! 👋"
    }
    requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=general_payload)

    return "OK", 200

# Flask startup
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)