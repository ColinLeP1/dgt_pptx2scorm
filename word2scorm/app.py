import streamlit as st
import os
import shutil
import zipfile
import uuid
import re
import chardet
from fpdf import FPDF
from pathlib import Path
from docx2pdf import convert
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

# Dossiers
EXPORTS_DIR = "exports"
os.makedirs(EXPORTS_DIR, exist_ok=True)

# Fonction time -> seconds
def parse_time_to_seconds(time_str):
    if not re.match(r"^\d{2}:\d{2}:\d{2}$", time_str):
        raise ValueError("Format invalide. Utilisez HH:MM:SS")
    h, m, s = map(int, time_str.split(":"))
    if h > 12 or m >= 60 or s >= 60:
        raise ValueError("Durée invalide : max 12h, 59min, 59s")
    return h * 3600 + m * 60 + s

# Liste des formats autorisés
SUPPORTED_EXTENSIONS = {
    "Textes": ["pdf", "docx", "doc", "rtf", "txt", "odt", "pages"],
    "Présentations": ["pptx", "odp"],
    "Tableurs": ["xls","xlsx","xlsm","xltx","xltm","xlsb","ods","numbers","csv"]
}
# Aplatit les extensions dans un seul tableau
allowed_extensions = [ext for group in SUPPORTED_EXTENSIONS.values() for ext in group] 

# Détection du type de fichier
def detect_file_category(extension):
    for category, ext_list in SUPPORTED_EXTENSIONS.items():
        if extension.lower() in ext_list:
            return category
    return "Autre"

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

def create_index_html_by_type(file_name, category):
    # Affichage universel en iframe PDF
    return f"""<!DOCTYPE html>
<html>
  <head><meta charset="UTF-8"><title>Visionneur PDF</title></head>
  <body style="margin:0;padding:0;height:100vh;">
    <iframe src="{file_name}" style="width:100%;height:100%;" type="application/pdf"></iframe>
  </body>
</html>
"""

def convert_text_to_pdf(input_path, output_path):
    # Détecter l'encodage
    with open(input_path, 'rb') as f:
        rawdata = f.read()
    result = chardet.detect(rawdata)
    encoding = result['encoding'] if result['encoding'] else 'utf-8'

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    story = []
    with open(input_path, "r", encoding=encoding, errors="replace") as file:
        for line in file:
            line = line.strip()
            if line:
                story.append(Paragraph(line, normal_style))
                story.append(Spacer(1, 6))  # espace entre paragraphes

    doc.build(story)
    return output_path


def generate_scorm_package(uploaded_file, scorm_version, scorm_title, duration_seconds):
    temp_dir = Path(EXPORTS_DIR) / f"scorm_{uuid.uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    original_filename = uploaded_file.name
    extension = original_filename.split(".")[-1].lower()
    category = detect_file_category(extension)
    file_path = temp_dir / original_filename

    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    viewer_file = original_filename
    pdf_path = None

    if category == "Textes":
        if extension == "docx":
            pdf_path = convert_docx_to_pdf(str(file_path), str(temp_dir))
        else:
            # Conversion des autres formats texte en PDF simple
            text_pdf_path = temp_dir / f"{Path(original_filename).stem}.pdf"
            try:
                convert_text_to_pdf(str(file_path), str(text_pdf_path))
                pdf_path = text_pdf_path
            except Exception as e:
                raise RuntimeError(f"Échec de conversion en PDF : {e}")

        if pdf_path:
            viewer_file = Path(pdf_path).name

    # Créer index.html selon la catégorie
    index_html = create_index_html_by_type(viewer_file, category)
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

scorm_version = st.radio("Version SCORM :", ["SCORM 1.2", "SCORM 2004"])

uploaded_file = st.file_uploader(
    "Importer un document (Texte, Tableur, Présentation)", 
    type=allowed_extensions
)

with st.expander("📄 Types de fichiers supportés par catégorie"):
    for category, extensions in SUPPORTED_EXTENSIONS.items():
        st.markdown(f"- **{category}** : {', '.join(f'.{ext}' for ext in extensions)}")

if uploaded_file:
    default_title = Path(uploaded_file.name).stem
    scorm_title = st.text_input("Titre du module SCORM :", value=default_title)
    
    default_time = "00:10:00"
    time_input = st.text_input("⏱️ Temps avant validation automatique (HH:MM:SS)", value=default_time)

    try:
        duration_seconds = parse_time_to_seconds(time_input)
    except ValueError as ve:
        st.error(f"⛔ {ve}")
        st.stop()
    
    if st.button("🎁 Générer le SCORM"):
        with st.spinner("Création du package SCORM..."):
            try:
                zip_path = generate_scorm_package(uploaded_file, scorm_version, scorm_title, duration_seconds)
                st.success("SCORM généré avec succès ✅")
                with open(zip_path, "rb") as f:
                    st.download_button("📥 Télécharger le package SCORM", f, file_name=zip_path.name)
            except Exception as e:
                st.error(f"Erreur : {e}")
else:
    st.info("Veuillez importer un fichier pour démarrer.")
