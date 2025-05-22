import streamlit as st
import os
import zipfile
import uuid
import shutil
import re
from PyPDF2 import PdfReader

# Crée un dossier temporaire avec fichier SCORM
def create_scorm_package(title, pdf_file, seconds_required, scorm_version):
    uid = str(uuid.uuid4())
    folder = f"scorm_{uid}"
    os.makedirs(folder, exist_ok=True)

    pdf_path = os.path.join(folder, "document.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_file.read())

    minutes_ms = seconds_required * 60 * 1000

    # Script SCORM (JS) simplifié
    scorm_script = """
<script>
function findAPI(win) {
    var attempts = 0;
    while ((win.API == null) && (win.parent != null) && (win.parent != win)) {
        attempts++;
        if (attempts > 10) return null;
        win = win.parent;
    }
    return win.API;
}

function completeAfterDelay() {
    var api = findAPI(window);
    if (api) {
        api.LMSInitialize("");
        setTimeout(() => {
            api.LMSSetValue("cmi.core.lesson_status", "completed");
            api.LMSCommit("");
            api.LMSFinish("");
            console.log("Cours terminé (délai écoulé)");
        }, TIME_TO_COMPLETE);
    } else {
        console.warn("API SCORM non trouvée");
    }
}
window.onload = completeAfterDelay;
</script>
"""

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{ font-family: sans-serif; text-align: center; padding: 20px; }}
    iframe {{ width: 100%; height: 600px; border: 1px solid #ccc; }}
    #timer {{ font-size: 2em; margin: 20px 0; color: #d9534f; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>Veuillez lire le document ci-dessous. Le module sera marqué comme complété après {seconds_required} seconds.</p>
  <div id="timer">Temps restant : {seconds_required}</div>
  <iframe src="document.pdf"></iframe>

  <script>
    const TIME_TO_COMPLETE = {seconds_required * 60}; // en secondes
    const SCORM_VERSION = "{scorm_version}";
    let remaining = TIME_TO_COMPLETE;

    function formatTime(seconds) {{
      const m = Math.floor(seconds / 60).toString().padStart(2, '0');
      const s = (seconds % 60).toString().padStart(2, '0');
      return `${{m}}:${{s}}`;
    }}

    function updateTimer() {{
      const timerDiv = document.getElementById("timer");
      if (remaining > 0) {{
        timerDiv.innerText = "Temps restant : " + formatTime(remaining);
        remaining--;
      }} else {{
        completeScorm();
        timerDiv.innerText = "✅ Temps écoulé, module complété.";
        clearInterval(interval);
      }}
    }}

    function findAPI(win) {{
      while ((win.API == null) && (win.parent != null) && (win.parent != win)) {{
        win = win.parent;
      }}
      return win.API;
    }}

    function findAPI2004(win) {{
      while ((win.API_1484_11 == null) && (win.parent != null) && (win.parent != win)) {{
        win = win.parent;
      }}
      return win.API_1484_11;
    }}

    function completeScorm() {{
      let api = SCORM_VERSION === "1.2" ? findAPI(window) : findAPI2004(window);
      if (!api) {{
        console.warn("API SCORM non trouvée");
        return;
      }}

      if (SCORM_VERSION === "1.2") {{
        api.LMSInitialize("");
        api.LMSSetValue("cmi.core.lesson_status", "completed");
        api.LMSCommit("");
        api.LMSFinish("");
      }} else {{
        api.Initialize("");
        api.SetValue("cmi.completion_status", "completed");
        api.Commit("");
        api.Terminate("");
      }}
    }}

    const interval = setInterval(updateTimer, 1000);
    updateTimer();
  </script>
</body>
</html>
"""


    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # SCORM manifest minimal
    manifest = f'''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="com.example.pdf.scorm" version="1.0"
    xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
    xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2
    imscp_rootv1p1p2.xsd
    http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <organizations default="ORG1">
    <organization identifier="ORG1">
      <title>{title}</title>
      <item identifier="ITEM1" identifierref="RES1">
        <title>{title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES1" type="webcontent" adlcp:scormtype="sco" href="index.html">
      <file href="index.html"/>
      <file href="document.pdf"/>
    </resource>
  </resources>
</manifest>'''

    with open(os.path.join(folder, "imsmanifest.xml"), "w", encoding="utf-8") as f:
        f.write(manifest)

    zip_filename = f"{folder}.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for root, _, files in os.walk(folder):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), folder))

    shutil.rmtree(folder)
    return zip_filename

# App Streamlit
st.title("📘 Convertisseur PDF vers SCORM avec condition de temps")

pdf_file = st.file_uploader("Téléversez un fichier PDF", type=["pdf"])
default_title = ""
if pdf_file:
    default_title = os.path.splitext(pdf_file.name)[0]
title = st.text_input("Titre du module", default_title)
scorm_version = st.radio("Version SCORM", ["1.2", "2004"])
time_input = st.text_input("Temps de complétion requis (HH:MM:SS)", "00:05:00")

def parse_hms(hms_str):
    match = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", hms_str)
    if not match:
        return None
    h, m, s = map(int, match.groups())
    return h * 3600 + m * 60 + s

total_seconds = parse_hms(time_input)
if total_seconds is None:
    st.error("Format invalide. Veuillez utiliser HH:MM:SS.")

if pdf_file and total_seconds and st.button("Générer le package SCORM"):
    try:
        reader = PdfReader(pdf_file)
        num_pages = len(reader.pages)

        zip_path = create_scorm_package(title, pdf_file, total_seconds, scorm_version)

        with open(zip_path, "rb") as f:
            st.download_button("📥 Télécharger le SCORM", f, file_name=f"{title.replace(' ', '_')}.zip")
    except Exception as e:
        st.error(f"Erreur lors du traitement du PDF : {e}")
