import streamlit as st
import json
import os
from openai import OpenAI

# Initialise OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Sportscode Code Window", layout="wide")
st.title("🧠 AI Code Window Generator (Sportscode-style)")

prompt = st.text_area("📝 Describe your tactical scenario:", height=100)

# --- Helper Functions ---
def get_colour_for_row(name):
    name = name.lower()
    if "goal" in name: return "#d7263d"
    elif "shot" in name: return "#f49d37"
    elif "corner" in name: return "#3f88c5"
    elif "cross" in name or "cutback" in name: return "#ffce00"
    elif "turnover" in name: return "#9c89b8"
    elif "press" in name: return "#6a4c93"
    elif "save" in name: return "#595959"
    else: return "#444"

def categorise_row(name):
    name = name.lower()
    if "turnover" in name: return "Turnovers"
    elif "restart" in name or "goal kick" in name: return "Restarts"
    elif "shot" in name or "goal" in name or "save" in name: return "Shots"
    elif "press" in name: return "Pressing"
    elif "cross" in name or "set piece" in name: return "Set Pieces"
    elif "1v1" in name or "interception" in name: return "Player Actions"
    else: return "Other"

def render_code_window(rows):
    st.markdown("<h3 style='margin-top:2rem;'>🎛️ Code Window Layout</h3>", unsafe_allow_html=True)

    grouped = {}
    for row in rows:
        category = categorise_row(row.get("name", "Other"))
        grouped.setdefault(category, []).append(row)

    for category, items in grouped.items():
        st.markdown(f"<h4 style='margin-top:2rem;background:#eee;padding:6px;border-radius:4px;'>{category}</h4>", unsafe_allow_html=True)

        blocks = ""
        for row in items:
            name = row.get("name", "Unnamed")
            colour = get_colour_for_row(name)
            blocks += f"""
            <div style=\"background-color:{colour};padding:12px;border-radius:6px;
                        color:white;text-align:center;font-weight:bold;font-family:sans-serif;\">
                {name}
            </div>
            """

        full_html = f"""
        <div style=\"display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;\">
            {blocks}
        </div>
        """
        st.markdown(full_html, unsafe_allow_html=True)

def render_field_map(rows):
    st.markdown("<h3 style='margin-top:3rem;'>📍 XY Tagging Zones</h3>", unsafe_allow_html=True)

    pitch_html = """
    <div style='position:relative;width:100%;max-width:800px;aspect-ratio:2/1;
                background-image:url("https://upload.wikimedia.org/wikipedia/commons/7/7a/Football_pitch_pitch_pattern.svg");
                background-size:cover;border:2px solid #aaa;margin-bottom:20px;'>
    """

    zones = {
        "Left Wing": (15, 40), "Right Wing": (75, 40),
        "Centre Mid": (45, 50), "Final Third": (45, 20), "Defensive Third": (45, 80)
    }

    for row in rows:
        name = row.get("name", "Unnamed")
        label = ", ".join(row.get("labels", []))
        lower = name.lower()

        if "left" in lower:
            x, y = zones["Left Wing"]
        elif "right" in lower:
            x, y = zones["Right Wing"]
        elif "final" in lower:
            x, y = zones["Final Third"]
        elif "defen" in lower:
            x, y = zones["Defensive Third"]
        else:
            x, y = zones["Centre Mid"]

        pitch_html += f"""
        <div style='position:absolute;left:{x}%;top:{y}%;transform:translate(-50%,-50%);
                    background:rgba(0,0,0,0.75);color:white;padding:6px 10px;border-radius:6px;
                    font-size:0.8em;text-align:center;max-width:140px;'>
            <strong>{name}</strong><br>
            <span style='font-size:0.7em'>{label}</span>
        </div>
        """

    pitch_html += "</div>"
    st.markdown(pitch_html, unsafe_allow_html=True)

# --- Run the Generator ---
if st.button("Generate"):
    if not prompt.strip():
        st.warning("Please enter a tactical scenario.")
    else:
        with st.spinner("Thinking..."):
            try:
                res = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": """
You are a Hudl Sportscode expert. Always respond with a valid JSON object in this format:
{
  "rows": [
    {
      "name": "High Press Trigger",
      "labels": ["Left Zone", "Pass Forced", "Interception"],
      "colour": "Red"
    },
    {
      "name": "Cutback Opportunity",
      "labels": ["Zone 14", "Player", "Assist Type"],
      "colour": "Yellow"
    }
  ]
}
""" },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=700
                )

                raw = res.choices[0].message.content.strip()

                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    st.error("⚠️ Could not interpret AI response. Please try again.")
                    st.stop()

                rows = parsed.get("rows", [])
                if not rows:
                    st.error("No rows found in the output.")
                else:
                    render_code_window(rows)
                    render_field_map(rows)

            except Exception as e:
                st.error(f"❌ Error: {e}")
