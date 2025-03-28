from flask import Flask, request, jsonify
import os
import openai
import hashlib
import hmac
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

openai.api_key = OPENAI_API_KEY

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
    user_question = request.form.get("text")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Collabor·AI·te, a friendly, smart AI Slack assistant that answers AI/ML questions clearly and with encouragement."},
                {"role": "user", "content": user_question}
            ]
        )
        answer = response['choices'][0]['message']['content']
        return jsonify({
            "response_type": "in_channel",
            "text": f"🤖 *Collabor·AI·te says:*\n{answer}"
        })
    except Exception as e:
        print("OpenAI Error:", e)
        return jsonify({
            "response_type": "ephemeral",
            "text": "⚠️ Sorry, something went wrong trying to process that question."
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)