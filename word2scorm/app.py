import streamlit as st
import os
import shutil
import zipfile
import uuid
from pathlib import Path
import urllib.parse

# Constantes
SCORM_TEMPLATE_DIR = "scorm_package"
EXPORTS_DIR = "exports"
os.makedirs(EXPORTS_DIR, exist_ok=True)

# Fonction pour créer le manifest SCORM
def create_scorm_manifest(scorm_version, title="Document SCORM"):
    identifier = f"scorm_{uuid.uuid4()}"
    manifest = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{identifier}" version="1.0"
          xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 
          ims_xml.xsd 
          http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>{"1.2" if scorm_version == "SCORM 1.2" else "2004 3rd Edition"}</schemaversion>
  </metadata>
  <organizations default="org1">
    <organization identifier="org1">
      <title>{title}</title>
      <item identifier="item1" identifierref="res1">
        <title>{title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res1" type="webcontent" adlcp:scormtype="sco" href="index.html">
      <file href="index.html"/>
    </resource>
  </resources>
</manifest>
"""
    return manifest

# Fonction pour créer la page HTML avec visionneur
def create_index_html(file_name, file_type):
    if file_type == "PDF":
        return f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>SCORM Viewer - PDF</title>
  </head>
  <body>
    <h2>Document PDF</h2>
    <iframe src="{file_name}" width="100%" height="600px"></iframe>
  </body>
</html>
"""
    elif file_type == "DOCX":
        office_url = f"https://view.officeapps.live.com/op/embed.aspx?src={{SCORM_FILE_URL}}"
        return f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>SCORM Viewer - Word</title>
  </head>
  <body>
    <h2>Document Word</h2>
    <iframe src="{office_url}" width="100%" height="600px"></iframe>
    <p>⚠️ Le fichier DOCX doit être hébergé en ligne pour que l’aperçu fonctionne.</p>
  </body>
</html>
""".replace("{{SCORM_FILE_URL}}", file_name)

# Fonction de création du SCORM ZIP
def generate_scorm_package(uploaded_file, file_type, scorm_version):
    # Créer répertoire temporaire
    temp_dir = Path(f"{EXPORTS_DIR}/scorm_{uuid.uuid4().hex}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Copier le fichier
    file_path = temp_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    # Créer index.html
    index_html = create_index_html(uploaded_file.name, file_type)
    (temp_dir / "index.html").write_text(index_html, encoding="utf-8")

    # Créer imsmanifest.xml
    manifest_xml = create_scorm_manifest(scorm_version, title=uploaded_file.name)
    (temp_dir / "imsmanifest.xml").write_text(manifest_xml, encoding="utf-8")

    # Créer le ZIP
    zip_path = Path(EXPORTS_DIR) / f"{uploaded_file.name.replace('.', '_')}_SCORM.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                filepath = Path(root) / file
                zipf.write(filepath, arcname=filepath.relative_to(temp_dir))

    # Nettoyage temporaire
    shutil.rmtree(temp_dir)
    return zip_path

# --- Streamlit UI ---
st.set_page_config(page_title="Générateur de SCORM", layout="centered")
st.title("📦 Générateur de SCORM avec visionneur")

file_type = st.selectbox("Type de fichier :", ["PDF", "DOCX"])
scorm_version = st.radio("Version SCORM :", ["SCORM 1.2", "SCORM 2004"])

uploaded_file = None
if file_type == "PDF":
    uploaded_file = st.file_uploader("Importer un fichier PDF", type=["pdf"])
else:
    uploaded_file = st.file_uploader("Importer un fichier Word (.docx)", type=["docx", "doc"])

if uploaded_file:
    if st.button("🎁 Générer le SCORM"):
        with st.spinner("Création du package SCORM..."):
            zip_path = generate_scorm_package(uploaded_file, file_type, scorm_version)
            st.success("SCORM généré avec succès ✅")
            with open(zip_path, "rb") as f:
                st.download_button("📥 Télécharger le package SCORM", f, file_name=zip_path.name)

else:
    st.info("Veuillez importer un fichier pour démarrer.")

