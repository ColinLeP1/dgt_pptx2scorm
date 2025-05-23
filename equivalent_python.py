import streamlit as st
import re
import os
import tempfile
import shutil
import zipfile

st.set_page_config(page_title="Générateur SCORM PDF", layout="centered")
st.title("📦 Générateur de SCORM à partir d’un PDF")

uploaded_file = st.file_uploader("Téléversez un fichier PDF", type="pdf")

# Titre unique utilisé pour le module et le nom de fichier
default_title = uploaded_file.name.replace(".pdf", "") if uploaded_file else "Module_SCORM"
scorm_title = st.text_input("Titre du module SCORM", value=default_title)
scorm_filename = re.sub(r"[^\w\-]", "_", scorm_title)

# Timer
time_str = st.text_input("Temps de visualisation requis (HH:MM:SS)", "00:05:00")

def parse_hms(hms_str):
    match = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", hms_str)
    if not match:
        return None
    h, m, s = map(int, match.groups())
    return h * 3600 + m * 60 + s

seconds_required = parse_hms(time_str)
if seconds_required is None:
    st.error("⛔ Format invalide. Utilisez HH:MM:SS.")
elif seconds_required > 86400:
    st.error("⛔ Le temps ne doit pas dépasser 24h.")

# Critère de validation
validation_criteria = st.selectbox(
    "Critères de validation",
    options=[
        "Lecture de toutes les pages",
        "Temps écoulé",
        "Lecture + Temps écoulé"
    ],
    index=1
)

# Version SCORM (boutons exclusifs)
scorm_version = st.radio("Version SCORM", ["SCORM 1.2", "SCORM 2004"])
if not scorm_version:
    st.warning("Veuillez choisir une version SCORM.")

# Options téléchargement/impression
make_downloadable = st.checkbox("Autoriser le téléchargement du PDF", value=False)
make_printable = st.checkbox("Autoriser l’impression du PDF", value=False)

# Génération du SCORM
if st.button("📁 Générer le SCORM"):
    if not uploaded_file:
        st.error("Veuillez téléverser un fichier PDF.")
    elif seconds_required is None or seconds_required > 86400:
        st.error("Le timer est invalide.")
    else:
        with st.spinner("📦 Création du package SCORM..."):
            temp_dir = tempfile.mkdtemp()
            pdf_filename = uploaded_file.name
            pdf_path = os.path.join(temp_dir, pdf_filename)

            # Sauvegarde du PDF
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())

            # Préparation HTML
            html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{scorm_title}</title>
  <style>
    body {{ font-family: sans-serif; background: #f8f9fa; padding: 20px; }}
    h1 {{ color: #333; }}
    #timer {{ font-size: 20px; font-weight: bold; margin-bottom: 15px; color: darkblue; }}
    embed {{ width: 100%; height: 600px; border: 1px solid #ccc; }}
  </style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <div id="timer">Temps restant : {time_str}</div>
  <embed src="{pdf_filename}" type="application/pdf" 
         {'' if make_downloadable else 'oncontextmenu="return false"'}
         {'' if make_printable else 'style="pointer-events: none;"'}>
  <p><strong>Critère de validation sélectionné :</strong> {validation_criteria}</p>

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
        timerDiv.textContent = "✅ Temps écoulé - SCORM {scorm_version}";
        clearInterval(timer);
      }}
    }}

    updateTimer();
    const timer = setInterval(updateTimer, 1000);
  </script>
</body>
</html>"""

            # Écriture HTML
            with open(os.path.join(temp_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html_content)

            # Manifeste SCORM
            with open(os.path.join(temp_dir, "imsmanifest.xml"), "w", encoding="utf-8") as f:
                f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="MANIFEST-{scorm_filename}" version="1.0"
  xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
  xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_v1p3"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsglobal.org/xsd/imscp_v1p1
    http://www.imsglobal.org/xsd/imscp_v1p1.xsd
    http://www.adlnet.org/xsd/adlcp_v1p3
    http://www.adlnet.org/xsd/adlcp_v1p3.xsd">
  <organizations default="org1">
    <organization identifier="org1">
      <title>{scorm_title}</title>
      <item identifier="item1" identifierref="res1">
        <title>{scorm_title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res1" type="webcontent" adlcp:scormType="sco" href="index.html">
      <file href="index.html"/>
      <file href="{pdf_filename}"/>
    </resource>
  </resources>
</manifest>""")

            # Zip
            zip_path = os.path.join(temp_dir, f"{scorm_filename}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for folder, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith(".zip"):
                            continue
                        full_path = os.path.join(folder, file)
                        arcname = os.path.relpath(full_path, temp_dir)
                        zipf.write(full_path, arcname)

            # Téléchargement
            with open(zip_path, "rb") as f:
                st.success("✅ SCORM généré avec succès.")
                st.download_button(
                    label="📥 Télécharger le SCORM",
                    data=f,
                    file_name=f"{scorm_filename}.zip",
                    mime="application/zip"
                )

            shutil.rmtree(temp_dir)
