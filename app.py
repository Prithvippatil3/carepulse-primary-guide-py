from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3, os, re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static",
)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-deployment")
DB_PATH = os.path.join(BASE_DIR, "carepulse.db")

GUIDES = {
    "fever": {
        "title": "Fever",
        "summary": "Fever is a rise in body temperature and is often associated with an infection.",
        "care": ["Rest and avoid strenuous activity.", "Drink water regularly to prevent dehydration.", "Wear light clothing and keep the room comfortably cool.", "Monitor temperature and note how long the fever lasts."],
        "avoid": ["Do not use ice baths or alcohol rubs.", "Do not combine medicines with the same active ingredient.", "Do not take antibiotics unless prescribed by a qualified clinician."],
        "red": ["Difficulty breathing, confusion, seizure, stiff neck, severe dehydration, or a rash that does not fade when pressed.", "Seek prompt medical advice for persistent fever, worsening symptoms, pregnancy, weakened immunity, or fever in an infant."],
        "medicine": "Ask a pharmacist or clinician whether an over-the-counter fever medicine is appropriate for your age, health conditions and other medicines. Follow the product label."
    },
    "cough": {
        "title": "Cough",
        "summary": "A cough can occur with a cold, irritation, allergies or other conditions.",
        "care": ["Drink fluids regularly.", "Try warm drinks to soothe throat irritation.", "Avoid smoke, dust and other triggers.", "Rest and consider a clean humidifier if the air is dry."],
        "avoid": ["Do not give honey to children under 1 year.", "Avoid smoking and second-hand smoke.", "Do not use leftover antibiotics."],
        "red": ["Severe breathing difficulty, blue or grey lips, chest pain, coughing blood, or sudden choking: seek emergency care.", "Get medical advice for a cough that is persistent, worsening, or accompanied by high fever."],
        "medicine": "Cough products are not suitable for everyone, especially young children and people taking other medicines. Ask a pharmacist before use and follow the label."
    },
    "headache": {
        "title": "Headache",
        "summary": "Headaches have many possible causes, including dehydration, stress, missed meals and illness.",
        "care": ["Rest in a quiet, comfortable room.", "Drink water and eat regular meals.", "Take a break from screens and bright light.", "Note triggers, timing and associated symptoms."],
        "avoid": ["Avoid taking pain medicines more often than the label allows.", "Do not ignore a sudden, unusually severe headache."],
        "red": ["A sudden worst-ever headache, weakness, fainting, confusion, vision loss, seizure, fever with stiff neck, or headache after a serious head injury needs emergency assessment."],
        "medicine": "A pharmacist can help check whether an over-the-counter pain reliever is safe for you. Consider allergies, pregnancy, existing conditions and other medicines."
    },
    "acidity": {
        "title": "Acidity / Heartburn",
        "summary": "A burning feeling in the chest or upper abdomen can be related to acid reflux or indigestion.",
        "care": ["Eat smaller meals.", "Avoid lying down for 2–3 hours after eating.", "Notice and reduce foods or drinks that trigger symptoms.", "If symptoms occur at night, ask a clinician about safe positioning and options."],
        "avoid": ["Avoid large late-night meals and personal trigger foods.", "Do not repeatedly self-treat frequent symptoms without medical advice."],
        "red": ["Chest pressure or pain with sweating, breathlessness, faintness, or pain spreading to the arm, jaw or back may be a heart emergency. Seek emergency help."],
        "medicine": "Antacids and acid-reducing medicines are not suitable for everyone. Ask a pharmacist, particularly if symptoms are frequent or you take other medicines."
    },
    "loose motion": {
        "title": "Loose Motion / Diarrhoea",
        "summary": "Diarrhoea can cause loss of water and salts, so preventing dehydration is important.",
        "care": ["Use oral rehydration solution (ORS) prepared exactly as directed on the packet.", "Take frequent small sips of fluids.", "Continue light, tolerated meals.", "Wash hands carefully with soap and safe water."],
        "avoid": ["Avoid very sugary drinks as the main rehydration fluid.", "Do not use anti-diarrhoeal medicines for children unless advised by a clinician."],
        "red": ["Blood or black stool, severe abdominal pain, confusion, inability to keep fluids down, very little urine, or signs of severe dehydration require urgent care.", "Seek medical advice for infants, older adults, pregnancy, or persistent symptoms."],
        "medicine": "ORS is important for fluid replacement. Ask a clinician or pharmacist before using other medicines, especially for children or if fever or blood in stool is present."
    },
    "cold": {
        "title": "Common Cold",
        "summary": "A common cold is usually a viral upper-respiratory infection.",
        "care": ["Rest and drink enough fluids.", "Use saline nasal drops or spray if appropriate.", "Warm drinks may soothe a sore throat.", "Cover coughs and sneezes and wash hands regularly."],
        "avoid": ["Antibiotics do not treat common cold viruses.", "Avoid combining multiple cold products without checking their ingredients."],
        "red": ["Seek emergency help for severe breathing difficulty, chest pain, blue lips or confusion.", "Get medical advice for worsening symptoms, dehydration, persistent high fever or symptoms that do not improve."],
        "medicine": "Cold medicines may only relieve symptoms and can have age restrictions or interactions. Ask a pharmacist and follow the label."
    }
}

KEYWORDS = {
    "fever": ["fever", "temperature", "high temperature", "body heat"],
    "cough": ["cough", "throat irritation", "dry cough", "wet cough"],
    "headache": ["headache", "head pain", "migraine"],
    "acidity": ["acidity", "heartburn", "acid reflux", "indigestion", "burning stomach"],
    "loose motion": ["loose motion", "diarrhoea", "diarrhea", "watery stool"],
    "cold": ["cold", "runny nose", "sneezing", "blocked nose", "common cold"]
}
RED_FLAG_TERMS = [
    "can't breathe", "cannot breathe", "difficulty breathing", "chest pain",
    "chest pressure", "unconscious", "not responding", "seizure", "stroke",
    "face drooping", "weakness on one side", "severe bleeding", "coughing blood",
    "blue lips", "suicidal", "poisoning", "overdose"
]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symptoms TEXT NOT NULL,
            guide_key TEXT,
            created_at TEXT NOT NULL
        )""")

def identify_guide(text):
    text = text.lower()
    for key, words in KEYWORDS.items():
        if any(re.search(r'\b' + re.escape(word) + r'\b', text) for word in words):
            return key
    return None

@app.route("/")
def home():
    return render_template("index.html", guides=GUIDES)

@app.route("/guide", methods=["POST"])
def guide():
    symptoms = request.form.get("symptoms", "").strip()
    if not symptoms:
        return jsonify({"error": "Please describe your symptom first."}), 400
    if len(symptoms) > 1000:
        return jsonify({"error": "Please keep the description under 1000 characters."}), 400

    lowered = symptoms.lower()
    urgent = any(term in lowered for term in RED_FLAG_TERMS)
    key = identify_guide(symptoms)

    # Vercel Functions have an ephemeral/read-only deployment filesystem.
    # Keep local SQLite logging for development; use a hosted database for production logging.
    if not os.environ.get("VERCEL"):
        with db() as conn:
            conn.execute(
                "INSERT INTO consultations(symptoms, guide_key, created_at) VALUES (?, ?, ?)",
                (symptoms, key, datetime.now().isoformat(timespec="seconds"))
            )

    if urgent:
        return jsonify({
            "urgent": True,
            "title": "Possible emergency warning sign",
            "summary": "Your description includes a symptom that may need urgent assessment.",
            "red": ["Contact local emergency services now or go to the nearest emergency department. In India, call 112 for emergency assistance.", "Do not delay care to use this website."]
        })
    if not key:
        return jsonify({
            "unknown": True,
            "title": "More information is needed",
            "summary": "This guide does not have a suitable general-care entry for that description.",
            "care": ["Please contact a qualified healthcare professional for an assessment.", "If symptoms are severe, sudden or rapidly worsening, seek urgent medical care."]
        })
    return jsonify({"guide": GUIDES[key]})

@app.route("/admin/consultations")
def admin_consultations():
    # Basic demo view. Add authentication before exposing this route publicly.
    if os.environ.get("VERCEL"):
        rows = []  # Persistent consultation history requires an external database.
    else:
        with db() as conn:
            rows = conn.execute("SELECT * FROM consultations ORDER BY id DESC LIMIT 100").fetchall()
    return render_template("admin.html", rows=rows)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "CarePulse"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
