import streamlit as st
import os
import shutil
import zipfile
import uuid
from pathlib import Path
from docx2pdf import convert
import platform
st.write(f"Système détecté : {platform.system()}")

# Dossiers
EXPORTS_DIR = "exports"
os.makedirs(EXPORTS_DIR, exist_ok=True)

# Fonctions SCORM
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

def create_index_html(file_name):
    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>SCORM Viewer</title>
  </head>
  <body>
    <h2>Document</h2>
    <iframe src="{file_name}" width="100%" height="600px"></iframe>
  </body>
</html>
"""

def convert_docx_to_pdf(docx_path, output_dir):
    convert(docx_path, output_dir)
    pdf_path = os.path.splitext(docx_path)[0] + ".pdf"
    return pdf_path

def generate_scorm_package(uploaded_file, file_type, scorm_version, scorm_title):
    temp_dir = Path(EXPORTS_DIR) / f"scorm_{uuid.uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    original_filename = uploaded_file.name
    file_path = temp_dir / original_filename

    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    if file_type == "DOCX":
        pdf_path = convert_docx_to_pdf(str(file_path), str(temp_dir))
        viewer_file = Path(pdf_path).name
    else:
        viewer_file = original_filename

    # Créer index.html
    index_html = create_index_html(viewer_file)
    (temp_dir / "index.html").write_text(index_html, encoding="utf-8")

    # Créer imsmanifest.xml
    manifest_xml = create_scorm_manifest(scorm_version, title=scorm_title)
    (temp_dir / "imsmanifest.xml").write_text(manifest_xml, encoding="utf-8")

    # Créer le ZIP
    zip_path = Path(EXPORTS_DIR) / f"{original_filename.replace('.', '_')}_SCORM.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                filepath = Path(root) / file
                zipf.write(filepath, arcname=filepath.relative_to(temp_dir))

    shutil.rmtree(temp_dir)
    return zip_path

# --- UI Streamlit ---
st.set_page_config(page_title="SCORM Generator", layout="centered")
st.title("📦 Générateur de SCORM avec visionneur")

file_type = st.selectbox("Type de fichier :", ["PDF", "DOCX"])
scorm_version = st.radio("Version SCORM :", ["SCORM 1.2", "SCORM 2004"])

if file_type == "PDF":
    uploaded_file = st.file_uploader("Importer un fichier PDF", type=["pdf"])
else:
    uploaded_file = st.file_uploader("Importer un fichier Word (.docx)", type=["docx"])

if uploaded_file:
    default_title = Path(uploaded_file.name).stem
    scorm_title = st.text_input("Titre du module SCORM :", value=default_title)

    if st.button("🎁 Générer le SCORM"):
        with st.spinner("Création du package SCORM..."):
            try:
                zip_path = generate_scorm_package(uploaded_file, file_type, scorm_version, scorm_title)
                st.success("SCORM généré avec succès ✅")
                with open(zip_path, "rb") as f:
                    st.download_button("📥 Télécharger le package SCORM", f, file_name=zip_path.name)
            except Exception as e:
                st.error(f"Erreur : {e}")
else:
    st.info("Veuillez importer un fichier pour démarrer.")
