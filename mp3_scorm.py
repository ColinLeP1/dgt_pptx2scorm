import streamlit as st
import re
import os
import tempfile
import shutil
import zipfile

st.set_page_config(page_title="Générateur SCORM Audio", layout="centered")
st.title("🎵 Générateur de SCORM à partir d’un fichier MP3")

uploaded_file = st.file_uploader("Téléversez un fichier audio MP3", type=["mp3"])

default_title = uploaded_file.name.replace(".mp3", "") if uploaded_file else "Module_SCORM_Audio"
scorm_title = st.text_input("Titre du module SCORM (nom du ZIP)", value=default_title)
scorm_filename = re.sub(r"[^\w\-]", "_", scorm_title)

st.subheader("Version SCORM")
scorm_12 = st.checkbox("SCORM 1.2", key="scorm12")
scorm_2004 = st.checkbox("SCORM 2004", key="scorm2004")

if scorm_12 and scorm_2004:
    st.error("❌ Veuillez sélectionner une seule version SCORM.")
    disable_generate = True
elif not scorm_12 and not scorm_2004:
    st.warning("Veuillez sélectionner une version SCORM.")
    disable_generate = True
else:
    disable_generate = False

if st.button("📁 Générer le package SCORM", disabled=disable_generate):
    if not uploaded_file:
        st.error("Veuillez téléverser un fichier MP3.")
    elif scorm_12 == scorm_2004:
        st.error("Veuillez choisir une seule version SCORM.")
    else:
        scorm_version = "1.2" if scorm_12 else "2004"
        with st.spinner("📦 Création du package SCORM..."):
            temp_dir = tempfile.mkdtemp()

            # Sauvegarder le MP3 dans temp_dir
            mp3_filename = uploaded_file.name
            mp3_path = os.path.join(temp_dir, mp3_filename)
            with open(mp3_path, "wb") as f:
                f.write(uploaded_file.read())

            # Génération index.html avec lecteur audio
            html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />
<title>{scorm_title}</title>
<style>
  body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 40px; text-align: center; }}
  h1 {{ color: #333; margin-bottom: 30px; }}
  audio {{ width: 80%; max-width: 600px; outline: none; }}
</style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <audio controls>
    <source src="{mp3_filename}" type="audio/mpeg">
    Votre navigateur ne supporte pas la lecture audio.
  </audio>
</body>
</html>
"""
            with open(os.path.join(temp_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html_content)

            # Génération imsmanifest.xml
            if scorm_12:
                manifest_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="com.example.{scorm_filename}" version="1"
    xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
    xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2
    imscp_rootv1p1p2.xsd
    http://www.adlnet.org/xsd/adlcp_rootv1p2
    adlcp_rootv1p2.xsd">

  <organizations default="ORG-1">
    <organization identifier="ORG-1" structure="hierarchical">
      <title>{scorm_title}</title>
      <item identifier="ITEM-1" identifierref="RES-1">
        <title>{scorm_title}</title>
      </item>
    </organization>
  </organizations>

  <resources>
    <resource identifier="RES-1" type="webcontent" adlcp:scormType="sco" href="index.html">
      <file href="index.html"/>
      <file href="{mp3_filename}"/>
    </resource>
  </resources>
</manifest>
"""
            else:
                # SCORM 2004
                manifest_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="com.example.{scorm_filename}" version="1"
  xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
  xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_v1p3"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsglobal.org/xsd/imscp_v1p1
  imscp_v1p1.xsd
  http://www.adlnet.org/xsd/adlcp_v1p3
  adlcp_v1p3.xsd">

  <organizations default="ORG-1">
    <organization identifier="ORG-1" structure="hierarchical">
      <title>{scorm_title}</title>
      <item identifier="ITEM-1" identifierref="RES-1">
        <title>{scorm_title}</title>
      </item>
    </organization>
  </organizations>

  <resources>
    <resource identifier="RES-1" type="webcontent" adlcp:scormType="sco" href="index.html">
      <file href="index.html"/>
      <file href="{mp3_filename}"/>
    </resource>
  </resources>
</manifest>
"""

            with open(os.path.join(temp_dir, "imsmanifest.xml"), "w", encoding="utf-8") as f:
                f.write(manifest_content)

            # Création du ZIP SCORM
            zip_filename = f"{scorm_filename}_SCORM_{scorm_version}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file == zip_filename:
                            continue
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)

            with open(zip_path, "rb") as f:
                zip_data = f.read()

            st.success(f"✅ SCORM prêt : {zip_filename}")
            st.download_button("⬇️ Télécharger le package SCORM", zip_data, file_name=zip_filename, mime="application/zip")

            shutil.rmtree(temp_dir)
