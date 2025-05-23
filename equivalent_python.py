import streamlit as st
import re
import os

st.set_page_config(page_title="Visionneuse PDF avec Timer", layout="centered")
st.title("📄 Visionneuse PDF avec Timer")

# 1. Charger un fichier PDF
uploaded_file = st.file_uploader("Choisissez un fichier PDF", type="pdf")

# 2. Entrée utilisateur pour le timer
time_str = st.text_input("Temps de visualisation (HH:MM:SS)", "00:05:00")

# 3. Convertir HH:MM:SS en secondes
def parse_hms(hms_str):
    match = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", hms_str)
    if not match:
        return None
    h, m, s = map(int, match.groups())
    return h * 3600 + m * 60 + s

seconds_required = parse_hms(time_str)
if seconds_required is None:
    st.error("⛔ Format invalide. Utilisez HH:MM:SS.")
    st.stop()

# 4. Sauvegarder temporairement le PDF
if uploaded_file:
    with st.spinner("Chargement du PDF..."):
        pdf_path = os.path.join("/tmp", uploaded_file.name)
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.read())

        # 5. Affichage HTML avec Timer JS
        st.markdown("### 📘 Aperçu du document")
        st.components.v1.html(f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <style>
                    #timer {{
                        font-size: 20px;
                        margin-bottom: 10px;
                        font-weight: bold;
                        color: darkgreen;
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
                <iframe src="data:application/pdf;base64,{uploaded_file.getvalue().decode('latin1').encode('base64').decode()}" type="application/pdf"></iframe>

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
                            timerDiv.textContent = "✅ Temps écoulé";
                            clearInterval(timer);
                        }}
                    }}
                    updateTimer();
                    const timer = setInterval(updateTimer, 1000);
                </script>
            </body>
            </html>
        """, height=700)
