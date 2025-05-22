import streamlit as st
import os
import zipfile
import uuid
import shutil
from PyPDF2 import PdfReader

def create_scorm_package(title, pdf_file, minutes_required, scorm_version):
    uid = str(uuid.uuid4())
    folder = f"scorm_{uid}"
    os.makedirs(folder, exist_ok=True)

    pdf_path = os.path.join(folder, "document.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_file.read())

    minutes_ms = minutes_required * 60 * 1000

    scorm_js = """
<script>
function findAPI(win) {
    while ((win.API == null) && (win.parent != null) && (win.parent != win)) {
        win = win.parent;
    }
    return win.API;
}

function findAPI2004(win) {
    while ((win.API_1484_11 == null) && (win.parent != null) && (win.parent != win)) {
        win = win.parent;
    }
    return win.API_1484_11;
}

function completeAfterDelay() {
    var scormVersion = SCORM_VERSION;
    var timeToComplete = TIME_TO_COMPLETE;

    var api = (scormVersion === "1.2") ? findAPI(window) : findAPI2004(window);

    if (api) {
        if (scormVersion === "1.2") {
            api.LMSInitialize("");
        } else {
            api.Initialize("");
        }

        setTimeout(() => {
            if (scormVersion === "1.2") {
                api.LMSSetValue("cmi.core.lesson_status", "completed");
                api.LMSCommit("");
                api.LMSFinish("");
            } else {
                api.SetValue("cmi.completion_status", "completed");
                api.Commit("");
                api.Terminate("");
            }
            console.log("SCORM complété après le délai.");
        }, timeToComplete);
    } else {
        console.warn("API SCORM non trouvée.");
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
</head>
<body>
    <h1>{title}</h1>
    <p>Ce module sera complété après {minutes_required} minute(s).</p>
    <iframe src="document.pdf" width="100%" height="600px"></iframe>
    <script>
    const SCORM_VERSION = "{scorm_version}";
    const TIME_TO_COMPLETE = {minutes_ms};
    </script>
    {scorm_js}
</body>
</html>
"""

    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

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

# Streamlit UI
st.title("📘 Convertisseur PDF vers SCORM avec condition de temps")

pdf_file = st.file_uploader("Téléversez un fichier PDF", type=["pdf"])
title = st.text_input("Titre du module", "Module SCORM")
scorm_version = st.radio("Version SCORM", ["1.2", "2004"])
minutes = st.slider("Temps de complétion requis (minutes)", min_value=1, max_value=60, value=5)

if pdf_file and st.button("Générer le package SCORM"):
    try:
        reader = PdfReader(pdf_file)
        zip_path = create_scorm_package(title, pdf_file, minutes, scorm_version)

        with open(zip_path, "rb") as f:
            st.success("SCORM généré avec succès ✅")
            st.download_button("📥 Télécharger le SCORM", f, file_name=f"{title.replace(' ', '_')}.zip")
    except Exception as e:
        st.error(f"Erreur : {e}")
