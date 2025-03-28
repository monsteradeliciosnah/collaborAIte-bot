from flask import Flask, request, jsonify
import os
import openai
import hashlib
import hmac
import time
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get secrets from environment
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Create Flask app
app = Flask(__name__)

# Optional: Slack request verification (recommended for production)
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

# Route for Slack slash command
@app.route("/askai", methods=["POST"])
def ask_ai():
    # Uncomment this block to enable Slack request verification
    # if not verify_slack_request(request):
    #     return "Unauthorized", 403

    user_question = request.form.get("text")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are Collabor·AI·te, a friendly, smart AI Slack assistant that answers AI/ML questions clearly and with encouragement."
                },
                {
                    "role": "user",
                    "content": user_question
                }
            ]
        )
        answer = response['choices'][0]['message']['content']
        return jsonify({
            "response_type": "in_channel",
            "text": f"🤖 *Collabor·AI·te says:*\n{answer}"
        })

    except Exception as e:
        error_trace = traceback.format_exc()
        print("OpenAI Error:", error_trace)
        return jsonify({
            "response_type": "ephemeral",
            "text": f"⚠️ Collabor·AI·te ran into an error: `{str(e)}`"
        })

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)