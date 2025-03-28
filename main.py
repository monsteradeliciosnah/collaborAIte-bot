from flask import Flask, request, jsonify
import os
import requests
import hashlib
import hmac
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)
PROJECTS_FILE = "projects.json"

# --- Slack verification ---
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

# --- Groq AI Q&A ---
@app.route("/askai", methods=["POST"])
def ask_ai():
    user_question = request.form.get("text")
    user_id = request.form.get("user_id")

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

        data = response.json()
        if "choices" not in data:
            raise ValueError("Groq response missing 'choices' key")

        answer = data["choices"][0]["message"]["content"]
        return jsonify({
            "response_type": "in_channel",
            "text": f"🤖 *Collabor·AI·te says:*\n{answer}"
        })

    except Exception as e:
        return jsonify({
            "response_type": "ephemeral",
            "text": f"⚠️ Collabor·AI·te ran into an error: {e}"
        })

# --- Project Tracker ---
def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return {}
    with open(PROJECTS_FILE, "r") as f:
        return json.load(f)

def save_projects(data):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/project", methods=["POST"])
def project_command():
    user_id = request.form.get("user_id")
    text = request.form.get("text").strip()
    command_parts = text.split(" ", 1)

    if len(command_parts) < 2:
        return jsonify({
            "response_type": "ephemeral",
            "text": "⚠️ Usage: `/project add|update|list [your text]`"
        })

    action, content = command_parts
    projects = load_projects()

    if action == "add":
        projects[user_id] = {
            "description": content,
            "updates": []
        }
        save_projects(projects)
        return jsonify({
            "response_type": "in_channel",
            "text": f"📌 <@{user_id}> just added a new project:\n> *{content}*"
        })

    elif action == "update":
        if user_id not in projects:
            return jsonify({
                "response_type": "ephemeral",
                "text": "🚫 You don’t have a project yet. Use `/project add` first!"
            })
        projects[user_id]["updates"].append(content)
        save_projects(projects)
        return jsonify({
            "response_type": "in_channel",
            "text": f"🔄 <@{user_id}> posted a project update:\n> {content}"
        })

    elif action == "list":
        messages = []
        for uid, entry in projects.items():
            msg = f"👤 <@{uid}>\n• *Project*: {entry['description']}"
            if entry["updates"]:
                updates = "\n    - " + "\n    - ".join(entry["updates"])
                msg += f"\n• Updates:{updates}"
            messages.append(msg)
        return jsonify({
            "response_type": "in_channel",
            "text": "🗂️ *Collabor·AI·te Project Tracker*\n\n" + "\n\n".join(messages) if messages else "No projects yet!"
        })

    else:
        return jsonify({
            "response_type": "ephemeral",
            "text": "❓ Unknown command. Use `add`, `update`, or `list`."
        })

# --- New User Welcome ---
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

    # Public welcome
    general_payload = {
        "channel": "#general",
        "text": f"🎉 Let’s welcome <@{user_id}> to [collabor·AI·te]! Say hi! 👋"
    }
    requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=general_payload)

    return "OK", 200

# --- Start the Flask server ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)