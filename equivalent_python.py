import streamlit as st
import re
import os
import tempfile
import shutil
import zipfile

st.set_page_config(page_title="Générateur SCORM PDF", layout="centered")
st.title("📦 Générateur de SCORM à partir d’un PDF")

uploaded_file = st.file_uploader("Téléversez un fichier PDF", type="pdf")

default_title = uploaded_file.name.replace(".pdf", "") if uploaded_file else "Module_SCORM"
scorm_title = st.text_input("Titre du module SCORM", value=default_title)
scorm_filename = st.text_input("Nom du fichier SCORM (zip)", value=re.sub(r"[^\w\-]", "_", scorm_title))

validation_criteria = st.selectbox(
    "Critère(s) de validation",
    options=["Lecture de toutes les pages", "Temps écoulé", "Lecture + Temps"]
)

if validation_criteria in ["Temps écoulé", "Lecture + Temps"]:
    time_str = st.text_input("Temps de visualisation requis (HH:MM:SS)", "00:05:00")
else:
    time_str = None

def parse_hms(hms_str):
    match = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", hms_str)
    if not match:
        return None
    h, m, s = map(int, match.groups())
    return h * 3600 + m * 60 + s

seconds_required = parse_hms(time_str) if time_str else 0
if time_str and seconds_required is None:
    st.error("⛔ Format du temps invalide. Utilisez HH:MM:SS.")
elif seconds_required and seconds_required > 86400:
    st.error("⛔ Le temps ne doit pas dépasser 24h.")

scorm_12 = st.checkbox("SCORM 1.2", value=True)
scorm_2004 = st.checkbox("SCORM 2004", value=False)

if scorm_12 and scorm_2004:
    scorm_2004 = False

if not scorm_12 and not scorm_2004:
    st.info("ℹ️ Veuillez choisir une version de SCORM.")

allow_print = st.checkbox("Autoriser l'impression du PDF", value=False)
allow_download = st.checkbox("Autoriser le téléchargement du PDF", value=False)

if st.button("📁 Générer le SCORM"):
    if not uploaded_file:
        st.error("Veuillez téléverser un fichier PDF.")
    elif (time_str and (seconds_required is None or seconds_required > 86400)):
        st.error("Le timer est invalide.")
    elif not (scorm_12 or scorm_2004):
        st.error("Veuillez choisir une version SCORM.")
    else:
        scorm_version = "1.2" if scorm_12 else "2004"
        with st.spinner("📦 Création du package SCORM..."):
            temp_dir = tempfile.mkdtemp()
            pdf_filename = uploaded_file.name
            pdf_path = os.path.join(temp_dir, pdf_filename)

            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())

            viewer_js_content = """
// viewer.js : contrôle barre d'outils PDF
document.addEventListener('DOMContentLoaded', function() {
  const embed = document.querySelector('embed');

  // Bloquer clic droit uniquement pour éviter menu contextuel PDF
  embed.addEventListener('contextmenu', function(e) {
    e.preventDefault();
  });

  // Fonction pour bloquer impression (désactive uniquement impression)
  function blockPrint() {
    window.onbeforeprint = function() {
      alert('L\'impression est désactivée pour ce document.');
      return false;
    };
  }

  // Fonction pour bloquer téléchargement (raccourcis clavier Ctrl+S / Cmd+S)
  function blockDownload() {
    document.addEventListener('keydown', function(e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        alert('Le téléchargement est désactivé.');
      }
      // Empêche aussi Ctrl+P (impression) si impression désactivée
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'p') {
        e.preventDefault();
        alert('L\'impression est désactivée.');
      }
    });
  }
"""

            if not allow_print:
                viewer_js_content += "\n  blockPrint();\n"
            if not allow_download:
                viewer_js_content += "\n  blockDownload();\n"

            viewer_js_content += "});"

            with open(os.path.join(temp_dir, "viewer.js"), "w", encoding="utf-8") as f:
                f.write(viewer_js_content)

            criteria_text = ""
            if validation_criteria == "Lecture de toutes les pages":
                criteria_text = "Critère de validation : Lecture de toutes les pages"
            elif validation_criteria == "Temps écoulé":
                criteria_text = f"Critère de validation : Temps écoulé ({time_str})"
            elif validation_criteria == "Lecture + Temps":
                criteria_text = f"Critère de validation : Lecture de toutes les pages + Temps écoulé ({time_str})"

            timer_js = ""
            timer_div = ""
            if validation_criteria in ["Temps écoulé", "Lecture + Temps"]:
                timer_div = f'<div id="timer" style="font-weight:bold; margin-bottom:15px; color: darkblue;">Temps restant : {time_str}</div>'
                timer_js = f"""
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
"""

            html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{scorm_title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
    h1 {{ color: #222; margin-bottom: 5px; }}
    #criteria {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: darkgreen; }}
    embed {{ width: 100%; height: 700px; border: 1px solid #ccc; }}
  </style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <div id="criteria">{criteria_text}</div>
  {timer_div}
  <embed src="{pdf_filename}" type="application/pdf" id="pdf_embed" />
  
  <script src="viewer.js"></script>
  {timer_js}
</body>
</html>"""

            with open(os.path.join(temp_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html_content)

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
                        if file.endswith(".zip"):
                            continue
                        full_path = os.path.join(folder, file)
                        arcname = os.path.relpath(full_path, temp_dir)
                        zipf.write(full_path, arcname)

            with open(zip_path, "rb") as f:
                st.success("✅ SCORM généré avec succès.")
                st.download_button(
                    label="📥 Télécharger le SCORM",
                    data=f,
                    file_name=f"{scorm_filename}.zip",
                    mime="application/zip"
                )

            shutil.rmtree(temp_dir)
