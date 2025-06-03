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

# Select pitch type before generating
pitch_type = st.selectbox("Select pitch type:", ["Soccer", "Basketball"], index=0)

# Select pitch type before generating


# Function to extract team names from the prompt
def extract_teams(text):
    match = re.search(r"([A-Z][a-z]+(?: [A-Z][a-z]+)?) vs ([A-Z][a-z]+(?: [A-Z][a-z]+)?)", text)
    return match.groups() if match else ("Team A", "Team B")

# Function to generate team logo URLs (basic fallback using Wikipedia)
def get_team_logo_url(team_name):
    import requests
    session = requests.Session()
    search_query = f"{team_name} crest"
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "piprop": "original",
        "titles": search_query
    }
    try:
        response = session.get(url=url, params=params)
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "original" in page:
                return page["original"]["source"]
    except Exception:
        pass
    return "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"
    search_key = team_name.strip().replace(" ", "_").replace("FC", "").replace("SC", "")
    return f"https://en.wikipedia.org/wiki/Special:Search?go=Go&search={search_key}+crest"

# Extract team names and logo URLs
team1, team2 = extract_teams(prompt) if prompt.strip() else ("Team A", "Team B")
logo1 = get_team_logo_url(team1)
logo2 = get_team_logo_url(team2)



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

def render_code_window(rows, pitch_type):
    st.markdown("<h3 style='margin-top:2rem;'>🎛️ Code Window Layout</h3>", unsafe_allow_html=True)

    grouped = {}
    for row in rows:
        name = row.get("name", "Unnamed")
        label = ", ".join(row.get("labels", []))
        lower = name.lower()

        if pitch_type == "Basketball":
            if "left wing" in lower:
                x, y = zones["Left Wing"]
            elif "right wing" in lower:
                x, y = zones["Right Wing"]
            elif "key" in lower:
                x, y = zones["Top of Key"]
            elif "paint" in lower:
                x, y = zones["Paint"]
            elif "corner" in lower and "left" in lower:
                x, y = zones["Corner Three Left"]
            elif "corner" in lower and "right" in lower:
                x, y = zones["Corner Three Right"]
            else:
                x, y = zones["Top of Key"]
        else:
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
    # Extract and show team names and logos only after prompt is submitted
    team1, team2 = extract_teams(prompt)
    logo1 = get_team_logo_url(team1)
    logo2 = get_team_logo_url(team2)

    t1, t2, t3 = st.columns([1, 4, 1])
    with t1:
        st.image(logo1, width=80)
    with t2:
        st.markdown(f"<h2 style='text-align:center;'>{team1} vs {team2}</h2>", unsafe_allow_html=True)
    with t3:
        st.image(logo2, width=80)
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
                    render_code_window(rows, pitch_type)
                    render_field_map(rows, pitch_type)

            except Exception as e:
                st.error(f"❌ Error: {e}")
