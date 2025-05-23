import streamlit as st
import re
import os
import tempfile
import shutil
import zipfile

st.set_page_config(page_title="Générateur SCORM PDF", layout="centered")
st.title("📦 Générateur de SCORM à partir d’un PDF")

# 1. Upload PDF
uploaded_file = st.file_uploader("Téléversez votre fichier PDF", type="pdf")

# 2. Choisir un nom pour le fichier SCORM
default_filename = uploaded_file.name.replace(".pdf", "") if uploaded_file else "module_scorm"
scorm_filename = st.text_input("Nom du fichier SCORM (sans extension)", value=default_filename)

# 3. Entrée du timer
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

# 4. Choix version SCORM
st.subheader("Version SCORM")
scorm_12 = st.checkbox("SCORM 1.2")
scorm_2004 = st.checkbox("SCORM 2004")

if scorm_12 and scorm_2004:
    st.error("❌ Veuillez sélectionner une seule version SCORM.")
elif not scorm_12 and not scorm_2004:
    st.info("ℹ️ Veuillez choisir une version de SCORM.")

# 5. Bouton pour générer SCORM
if st.button("📁 Générer le SCORM"):
    if not uploaded_file:
        st.error("Veuillez téléverser un fichier PDF.")
    elif seconds_required is None or seconds_required > 86400:
        st.error("Le timer est invalide.")
    elif scorm_12 == scorm_2004:
        st.error("Veuillez choisir une seule version SCORM.")
    else:
        scorm_version = "1.2" if scorm_12 else "2004"
        with st.spinner("Création du SCORM..."):

            temp_dir = tempfile.mkdtemp()
            pdf_name = uploaded_file.name
            pdf_path = os.path.join(temp_dir, pdf_name)

            # Enregistrement du PDF
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())

            # HTML sans iframe
            html_path = os.path.join(temp_dir, "index.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{scorm_filename}</title>
</head>
<body>
  <h1>{scorm_filename}</h1>
  <p>Temps de visualisation requis : {time_str}</p>
  <div id="timer">Temps restant : {time_str}</div>

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

    const timer = setInterval(updateTimer, 1000);
    updateTimer();
  </script>
</body>
</html>""")

            # imsmanifest.xml
            manifest_path = os.path.join(temp_dir, "imsmanifest.xml")
            with open(manifest_path, "w", encoding="utf-8") as f:
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
      <title>{scorm_filename}</title>
      <item identifier="item1" identifierref="resource1">
        <title>{scorm_filename}</title>
      </item>
    </organization>
  </organizations>

  <resources>
    <resource identifier="resource1" type="webcontent" adlcp:scormType="sco" href="index.html">
      <file href="index.html" />
      <file href="{pdf_name}" />
    </resource>
  </resources>
</manifest>""")

            # Créer ZIP SCORM
            zip_path = os.path.join(temp_dir, f"{scorm_filename}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith(".zip"): continue
                        full_path = os.path.join(root, file)
                        arcname = os.path.relpath(full_path, temp_dir)
                        zipf.write(full_path, arcname)

            # Télécharger
            with open(zip_path, "rb") as f:
                st.success("🎉 Package SCORM prêt !")
                st.download_button(
                    label="📥 Télécharger le SCORM",
                    data=f,
                    file_name=f"{scorm_filename}.zip",
                    mime="application/zip"
                )

            shutil.rmtree(temp_dir)
