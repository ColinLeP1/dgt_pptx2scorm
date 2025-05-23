import streamlit as st
import re
import os
import tempfile
import shutil
import zipfile

st.set_page_config(page_title="Générateur SCORM PDF", layout="centered")
st.title("📦 Générateur de SCORM à partir d’un PDF")

uploaded_file = st.file_uploader("Téléversez un fichier PDF", type="pdf")

# Critère de validation
validation_criteria = st.selectbox(
    "Critère de validation",
    ["Lecture de toutes les pages", "Temps écoulé", "Les deux"]
)

# Affichage conditionnel du timer
show_timer = validation_criteria in ["Temps écoulé", "Les deux"]
if show_timer:
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
else:
    time_str = ""
    seconds_required = 0

# SCORM version unique avec choix
scorm_version = st.radio("Version SCORM", ["SCORM 1.2", "SCORM 2004"])

# Nom du module = nom du fichier sans extension
default_title = uploaded_file.name.replace(".pdf", "") if uploaded_file else "Module_SCORM"
scorm_title = st.text_input("Titre du module SCORM", value=default_title)
scorm_filename = re.sub(r"[^\w\-]", "_", scorm_title)

# Choix d'impression / téléchargement du PDF
enable_download = st.checkbox("Autoriser le téléchargement du PDF")
enable_print = st.checkbox("Autoriser l'impression du PDF")

if st.button("📁 Générer le SCORM"):
    if not uploaded_file:
        st.error("Veuillez téléverser un fichier PDF.")
    elif show_timer and (seconds_required is None or seconds_required > 86400):
        st.error("Le timer est invalide.")
    else:
        version = "1.2" if scorm_version == "SCORM 1.2" else "2004"
        with st.spinner("📦 Création du package SCORM..."):

            temp_dir = tempfile.mkdtemp()
            pdf_filename = uploaded_file.name
            pdf_path = os.path.join(temp_dir, pdf_filename)

            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())

            # HTML
            html_content = f"""<!DOCTYPE html>
<html lang='fr'>
<head>
  <meta charset='UTF-8'>
  <title>{scorm_title}</title>
  <style>
    body {{ font-family: sans-serif; background: #f8f9fa; padding: 20px; }}
    h1 {{ color: #333; }}
    #timer, #criteria {{ font-size: 16px; font-weight: bold; margin-bottom: 10px; color: darkblue; }}
    embed {{ width: 100%; height: 600px; border: 1px solid #ccc; }}
  </style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <div id='criteria'>Critère de validation : {validation_criteria}</div>
  {'<div id="timer">Temps restant : ' + time_str + '</div>' if show_timer else ''}
  <embed id='pdf_viewer' src="{pdf_filename}" type="application/pdf">
  <script src="viewer.js"></script>
  {'<script>' + f"""
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
        timerDiv.textContent = "\u2705 Temps écoulé - SCORM {version}";
        clearInterval(timer);
      }}
    }}
    updateTimer();
    const timer = setInterval(updateTimer, 1000);
  """ + '</script>' if show_timer else ''}
</body>
</html>"""

            with open(os.path.join(temp_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html_content)

            with open(os.path.join(temp_dir, "viewer.js"), "w", encoding="utf-8") as f:
                f.write(f"""
document.addEventListener('DOMContentLoaded', function () {{
  const viewer = document.getElementById('pdf_viewer');
  if (viewer) {{
    viewer.setAttribute('disableprint', '{'false' if enable_print else 'true'}');
    viewer.setAttribute('disabledownload', '{'false' if enable_download else 'true'}');
  }}
}});
""")

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
      <file href="viewer.js"/>
    </resource>
  </resources>
</manifest>""")

            zip_path = os.path.join(temp_dir, f"{scorm_filename}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for folder, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith(".zip"): continue
                        full_path = os.path.join(folder, file)
                        arcname = os.path.relpath(full_path, temp_dir)
                        zipf.write(full_path, arcname)

            with open(zip_path, "rb") as f:
                st.success("\u2705 SCORM généré avec succès.")
                st.download_button(
                    label="\ud83d\udc45 Télécharger le SCORM",
                    data=f,
                    file_name=f"{scorm_filename}.zip",
                    mime="application/zip"
                )

            shutil.rmtree(temp_dir)
