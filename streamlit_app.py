import streamlit as st
import json
import os
from openai import OpenAI
import re

# Initialise OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Sportscode Code Window", layout="wide")
st.title("🧠 AI Code Window Generator (Sportscode-style)")

prompt = st.text_area("📝 Describe your tactical scenario:", height=100)

# Function to extract team names from the prompt
def extract_teams(text):
    match = re.search(r"([A-Z][a-z]+(?: [A-Z][a-z]+)?) vs ([A-Z][a-z]+(?: [A-Z][a-z]+)?)", text)
    return match.groups() if match else ("Team A", "Team B")

# Function to generate team logo URLs (basic fallback using Wikipedia)
def get_team_logo_url(team_name):
    team_key = team_name.replace(" ", "_")
    return f"https://upload.wikimedia.org/wikipedia/en/thumb/0/0e/{team_key}_crest.svg/120px-{team_key}_crest.svg.png"

# Extract team names and logo URLs
team1, team2 = extract_teams(prompt)
logo1 = get_team_logo_url(team1)
logo2 = get_team_logo_url(team2)

# Add team logo row
t1, t2, t3 = st.columns([1, 4, 1])
with t1:
    st.image(logo1, width=80)
with t2:
    st.markdown(f"<h2 style='text-align:center;'>{team1} vs {team2}</h2>", unsafe_allow_html=True)
with t3:
    st.image(logo2, width=80)

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

        html_blocks = []
        for row in items:
            name = row.get("name", "Unnamed")
            colour = get_colour_for_row(name)
            block_html = f"<div style='background-color:{colour};padding:12px;border-radius:6px;color:white;text-align:center;font-weight:bold;font-family:sans-serif;'>{name}</div>"
            html_blocks.append(block_html)

        grid_html = "<div style='display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;'>" + "".join(html_blocks) + "</div>"
        st.markdown(grid_html, unsafe_allow_html=True)

def render_field_map(rows):
    st.markdown("<h3 style='margin-top:3rem;'>📍 XY Tagging Zones</h3>", unsafe_allow_html=True)

    pitch_html = "<div style='position:relative;width:100%;max-width:800px;aspect-ratio:2/1;"
    pitch_html += "background-image:url(\"https://upload.wikimedia.org/wikipedia/commons/7/7a/Football_pitch_pitch_pattern.svg\");"
    pitch_html += "background-size:cover;border:2px solid #aaa;margin-bottom:20px;'>"

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

        pitch_html += f"<div style='position:absolute;left:{x}%;top:{y}%;transform:translate(-50%,-50%);"
        pitch_html += "background:rgba(0,0,0,0.75);color:white;padding:6px 10px;border-radius:6px;"
        pitch_html += "font-size:0.8em;text-align:center;max-width:140px;'>"
        pitch_html += f"<strong>{name}</strong><br><span style='font-size:0.7em'>{label}</span></div>"

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
