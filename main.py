from flask import Flask, request, jsonify
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-70b-8192"  # Or whichever is available
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

app = Flask(__name__)

PROJECTS_FILE = "projects.json"

# --- Utilities ---
def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return {}
    with open(PROJECTS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_projects(data):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def auto_tag(text):
    tags = []
    lower = text.lower()

    tag_map = {
        "huggingface": "#NLP",
        "transformer": "#NLP",
        "nlp": "#NLP",
        "chatbot": "#Chatbot",
        "gpt": "#Chatbot",
        "llm": "#LLM",
        "openai": "#LLM",
        "vision": "#Vision",
        "image": "#Vision",
        "cnn": "#Vision",
        "streamlit": "#DataViz",
        "dashboard": "#DataViz",
        "pandas": "#DataViz",
        "sql": "#Data",
        "infra": "#Infra",
        "kubernetes": "#Infra",
        "api": "#Infra"
    }

    for keyword, tag in tag_map.items():
        if keyword in lower and tag not in tags:
            tags.append(tag)

    return tags

# --- Routes ---
@app.route("/askai", methods=["POST"])
def ask_ai():
    user_question = request.form.get("text")
    user_id = request.form.get("user_id")

    print("🚀 Received Slack request to /askai")
    print("📩 User question:", user_question)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are Collabor·AI·te, a friendly, smart AI Slack assistant that answers AI/ML questions clearly and with encouragement."},
            {"role": "user", "content": user_question}
        ]
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        print("📦 Raw Response Code:", response.status_code)
        print("📦 Raw Response Text:", response.text)

        data = response.json()

        if "choices" not in data:
            raise ValueError("Groq response missing 'choices' key")

        answer = data['choices'][0]['message']['content']
        return jsonify({
            "response_type": "in_channel",
            "text": f"🤖 *Collabor·AI·te says:*\n{answer}"
        })
    except Exception as e:
        print("⚠️ Exception caught:", e)
        return jsonify({
            "response_type": "ephemeral",
            "text": f"⚠️ Collabor·AI·te ran into an error: {str(e)}"
        })

@app.route("/project", methods=["POST"])
def project_tracker():
    text = request.form.get("text")
    user_id = request.form.get("user_id")

    print("🔧 Project command from user:", user_id, ":", text)

    projects = load_projects()
    parts = text.split(" ", 1)
    action = parts[0].lower()
    content = parts[1] if len(parts) > 1 else ""

    if action == "add":
        tags = auto_tag(content)
        projects[user_id] = {
            "description": content,
            "updates": [],
            "tags": tags
        }
        save_projects(projects)
        return jsonify({
            "response_type": "in_channel",
            "text": f"📌 <@{user_id}> just added a new project:\n> *{content}*\n{' '.join(tags)}"
        })

    elif action == "update":
        if user_id not in projects:
            return jsonify({"text": "❗ You haven’t added a project yet. Use `/project add` first."})
        projects[user_id].setdefault("updates", []).append(content)
        tags = auto_tag(content)
        for tag in tags:
            if tag not in projects[user_id]["tags"]:
                projects[user_id]["tags"].append(tag)
        save_projects(projects)
        return jsonify({
            "response_type": "in_channel",
            "text": f"🔄 <@{user_id}> updated their project:\n> _{content}_\n{' '.join(tags)}"
        })

    elif action == "list":
        if not projects:
            return jsonify({"text": "🤷 No projects found yet."})
        msg = "📋 *Current Projects:*\n"
        for uid, entry in projects.items():
            msg += f"👤 <@{uid}>\n• *Project*: {entry['description']}"
            if entry.get("tags"):
                msg += f"\n• Tags: {' '.join(entry['tags'])}"
            if entry.get("updates"):
                for u in entry['updates']:
                    msg += f"\n    – {u}"
            msg += "\n\n"
        return jsonify({"text": msg})

    else:
        return jsonify({"text": "❓ Usage: `/project add|update|list your text here`"})

@app.route("/health", methods=["GET"])
def health():
    return "✅ Collabor·AI·te is alive!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)