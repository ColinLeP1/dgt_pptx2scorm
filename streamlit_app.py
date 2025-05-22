import streamlit as st
import zipfile
import os
import tempfile
import shutil
import re

st.set_page_config(page_title="Convertisseur PDF vers SCORM", layout="centered")
st.title("📄 Convertisseur PDF vers SCORM")

pdf_file = st.file_uploader("Téléversez un fichier PDF", type="pdf")

# Durée au format HH:MM:SS
time_input = st.text_input("Temps de complétion requis (HH:MM:SS)", "00:05:00")

def parse_hms(hms_str):
    match = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", hms_str)
    if not match:
        return None
    h, m, s = map(int, match.groups())
    return h * 3600 + m * 60 + s

total_seconds = parse_hms(time_input)
if total_seconds is None:
    st.error("⛔ Format invalide. Veuillez utiliser HH:MM:SS.")

default_title = os.path.splitext(pdf_file.name)[0] if pdf_file else ""
title = st.text_input("Titre du module", default_title)

scorm_version = st.selectbox("Version SCORM", ["1.2", "2004"])

if pdf_file and total_seconds and st.button("Générer le package SCORM"):
    with st.spinner("📦 Génération en cours..."):
        output_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        zip_path = output_zip.name

        def create_scorm_package(title, pdf_file, seconds_required, scorm_version):
            temp_dir = tempfile.mkdtemp()
            safe_title = re.sub(r'[^\w\-\. ]', '_', title)  # remplace caractères spéciaux par "_"
            pdf_path = os.path.join(temp_dir, f"{safe_title}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(pdf_file.read())

            html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 20px; }}
    #timer {{ font-size: 20px; margin-bottom: 10px; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>Veuillez lire le document ci-dessous. Le module sera marqué comme complété dès que le compteur atteindra 0.</p>
  <div id="timer">Temps restant : {seconds_required} secondes</div>
  

  <object data="document.pdf" type="application/pdf" width="100%" height="600px">
    <embed src="document.pdf" type="application/pdf" width="100%" height="600px" />
    <p>Votre navigateur ne peut pas afficher le PDF. <a href="document.pdf" target="_blank">Cliquez ici pour le télécharger</a>.</p>
  </object>

  <script>
    const SCORM_VERSION = "{scorm_version}";
    const TIME_TO_COMPLETE = {seconds_required};
    let remaining = TIME_TO_COMPLETE;

    function updateTimer() {{
      const timerDiv = document.getElementById("timer");

      if (remaining > 0) {{
        let text = "";

        if (remaining >= 3600) {{
          const h = Math.floor(remaining / 3600);
          const m = Math.floor((remaining % 3600) / 60);
          text = `Temps restant : ${{h}}h ${{m}}m`;
        }} else {{
          const m = Math.floor(remaining / 60);
          const s = remaining % 60;
          text = `Temps restant : ${{m.toString().padStart(2, '0')}}:${{s.toString().padStart(2, '0')}}`;
        }}

        timerDiv.innerText = text;
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

            with open(os.path.join(temp_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html)

            manifest = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="com.example.scorm" version="1.0"
          xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_v1p3"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.imsglobal.org/xsd/imscp_v1p1 
          imscp_v1p1.xsd
          http://www.adlnet.org/xsd/adlcp_v1p3 
          adlcp_v1p3.xsd">
  <organizations default="org1">
    <organization identifier="org1">
      <title>{title}</title>
      <item identifier="item1" identifierref="res1">
        <title>{title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res1" type="webcontent" adlcp:scormType="sco" href="index.html">
      <file href="index.html"/>
      <file href="document.pdf"/>
    </resource>
  </resources>
</manifest>
"""
            with open(os.path.join(temp_dir, "imsmanifest.xml"), "w", encoding="utf-8") as f:
                f.write(manifest)

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for foldername, _, filenames in os.walk(temp_dir):
                    for filename in filenames:
                        filepath = os.path.join(foldername, filename)
                        arcname = os.path.relpath(filepath, temp_dir)
                        zipf.write(filepath, arcname)

            shutil.rmtree(temp_dir)

        create_scorm_package(title, pdf_file, total_seconds, scorm_version)

        st.success("✅ Package SCORM généré avec succès.")
        with open(zip_path, "rb") as f:
            st.download_button("📥 Télécharger le package SCORM", f, file_name=f"{title}.zip")
