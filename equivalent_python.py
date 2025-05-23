import streamlit as st
import re
import os
import base64

st.set_page_config(page_title="Visionneuse PDF avec Timer SCORM", layout="centered")
st.title("📄 Visionneuse PDF avec Timer (SCORM Ready)")

# 1. Uploader le PDF
uploaded_file = st.file_uploader("Choisissez un fichier PDF", type="pdf")

# 2. Choisir la version SCORM
scorm_version = st.selectbox("Version SCORM", ["1.2", "2004"])

# 3. Entrée du timer
time_str = st.text_input("Temps de visualisation (HH:MM:SS)", "00:05:00")

# 4. Fonction pour valider et convertir
def parse_hms(hms_str):
    match = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", hms_str)
    if not match:
        return None
    h, m, s = map(int, match.groups())
    return h * 3600 + m * 60 + s

# 5. Conversion du temps
seconds_required = parse_hms(time_str)
if seconds_required is None:
    st.error("⛔ Format invalide. Utilisez HH:MM:SS.")
    st.stop()
elif seconds_required > 86400:
    st.error("⛔ Le temps ne doit pas dépasser 24 heures (HH:MM:SS <= 24:00:00).")
    st.stop()

# 6. Si fichier PDF fourni
if uploaded_file:
    st.success(f"📄 Fichier reçu : {uploaded_file.name}")
    
    # Convertir le fichier en base64 pour l'affichage
    b64_pdf = base64.b64encode(uploaded_file.read()).decode("utf-8")
    
    # Affichage HTML + Timer JS
    st.markdown("### 🕒 Aperçu avec Timer")
    st.components.v1.html(f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 10px;
                    background-color: #f8f9fa;
                }}
                #timer {{
                    font-size: 20px;
                    margin-bottom: 12px;
                    font-weight: bold;
                    color: darkblue;
                }}
                iframe {{
                    width: 100%;
                    height: 600px;
                    border: 1px solid #ccc;
                }}
            </style>
        </head>
        <body>
            <div id="timer">Temps restant : {time_str}</div>
            <iframe src="data:application/pdf;base64,{b64_pdf}" type="application/pdf"></iframe>

            <script>
                let remaining = {seconds_required};
                const timerDiv = document.getElementById("timer");

                function updateTimer() {{
                    if (remaining > 0) {{
                        const h = Math.floor(remaining / 3600);
                        const m = Math.floor((remaining % 3600) / 60);
                        const s = remaining % 60;
                        timerDiv.textContent = "Temps restant : " +
                            String(h).padStart(2, '0') + ":" +
                            String(m).padStart(2, '0') + ":" +
                            String(s).padStart(2, '0');
                        remaining--;
                    }} else {{
                        timerDiv.textContent = "✅ Temps écoulé (SCORM {scorm_version})";
                        clearInterval(timer);
                    }}
                }}

                updateTimer();
                const timer = setInterval(updateTimer, 1000);
            </script>
        </body>
        </html>
    """, height=700)
