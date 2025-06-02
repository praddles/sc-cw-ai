import streamlit as st
import openai
import json
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
st.set_page_config(page_title="AI Code Window Generator", layout="wide")
st.title("🧠 AI Code Window Generator for Sportscode")

prompt = st.text_area("📝 Describe your tactical scenario:", height=100)

# --- Utility Functions ---
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
    st.markdown("### 🧱 Code Window Layout")
    grid_html = "<div style='display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;'>"
    for row in rows:
        name = row.get("name", "Unnamed")
        labels = row.get("labels", [])
        colour = get_colour_for_row(name)
        label_html = " ".join(
            f"<div style='background:rgba(255,255,255,0.2);padding:2px 6px;border-radius:4px;font-size:0.75em;display:inline-block;margin-top:4px'>{l}</div>"
            for l in labels
        )
        grid_html += f"""
        <div style='background-color:{colour};padding:10px;border-radius:6px;color:white;font-family:sans-serif;'>
            <strong>{name}</strong>
            <div>{label_html}</div>
        </div>
        """
    grid_html += "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)

def render_pitch(rows):
    st.markdown("### 🗺️ Pitch View")
    pitch_html = """
    <div style='
        position: relative;
        width: 100%;
        max-width: 800px;
        aspect-ratio: 2 / 1;
        background-image: url("https://upload.wikimedia.org/wikipedia/commons/7/7a/Football_pitch_pitch_pattern.svg");
        background-size: cover;
        border: 2px solid #aaa;
        margin-bottom: 20px;
    '>
    """
    zones = {
        "Left Wing": (15, 40), "Right Wing": (75, 40),
        "Centre Mid": (45, 50), "Final Third": (45, 20), "Defensive Third": (45, 80)
    }
    for row in rows:
        name = row.get("name", "Unnamed")
        label = ", ".join(row.get("labels", []))
        lower = name.lower()
        if "left" in lower: x, y = zones["Left Wing"]
        elif "right" in lower: x, y = zones["Right Wing"]
        elif "final" in lower: x, y = zones["Final Third"]
        elif "defen" in lower: x, y = zones["Defensive Third"]
        else: x, y = zones["Centre Mid"]
        pitch_html += f"""
        <div style='
            position: absolute;
            left: {x}%;
            top: {y}%;
            transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.75);
            color: white;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 0.8em;
            text-align: center;
            max-width: 140px;
        '>
            <strong>{name}</strong><br>
            <span style='font-size: 0.7em'>{label}</span>
        </div>
        """
    pitch_html += "</div>"
    st.markdown(pitch_html, unsafe_allow_html=True)

# --- Run the AI Call ---
if st.button("Generate"):
    if not prompt.strip():
        st.warning("Please enter a tactical scenario.")
    else:
        with st.spinner("Thinking..."):
            try:
                res = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a Hudl Sportscode expert. Generate a JSON layout for a code window with row names, labels, and colour hints based on tactical prompts."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=700
                )
                raw = res.choices[0].message["content"]
                parsed = json.loads(raw)
                rows = parsed.get("rows", [])
                if not rows:
                    st.error("No rows found in the output.")
                else:
                    # Group and render
                    cat_rows = {}
                    for r in rows:
                        cat = categorise_row(r["name"])
                        cat_rows.setdefault(cat, []).append(r)
                    for cat, group in cat_rows.items():
                        st.markdown(f"### {cat}")
                        render_code_window(group)
                    render_pitch(rows)
                with st.expander("🔍 Raw JSON"):
                    st.json(parsed)
            except Exception as e:
                st.error(f"Error: {e}")
