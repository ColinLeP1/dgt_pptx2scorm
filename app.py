import streamlit as st
import zipfile
import tempfile
import shutil
import os

os.system("pip install PyPDF2")
from datetime import timedelta
from pathlib import Path
from PyPDF2 import PdfReader

st.title("Convertisseur PDF vers SCORM")

# 1. Upload du PDF
pdf_file = st.file_uploader("Uploader un fichier PDF", type="pdf")

# 2. Nom du module SCORM
module_title = st.text_input("Titre du module SCORM", value="Module SCORM")

# 3. Durée minimum à passer sur le document
min_duration_str = st.text_input("Durée minimale (hh:mm:ss)", value="00:05:00")

# 4. Format SCORM
scorm_version = st.selectbox("Version SCORM", ["1.2", "2004"])

# 5. Critère de complétude
completion_criteria = st.multiselect("Critères de complétude", ["temps", "pages"])

# 6. Bouton de génération
if st.button("Générer SCORM"):
    if pdf_file is None:
        st.error("Veuillez uploader un fichier PDF.")
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "document.pdf")
            with open(pdf_path, "wb") as f:
                f.write(pdf_file.read())

            h, m, s = map(int, min_duration_str.split(":"))
            min_seconds = int(timedelta(hours=h, minutes=m, seconds=s).total_seconds())

            pdf_reader = PdfReader(pdf_path)
            num_pages = len(pdf_reader.pages)

            scorm_base_path = os.path.join(os.path.dirname(__file__), "scorm_base")
            scorm_output_dir = os.path.join(tmpdir, "scorm_package")
            shutil.copytree(scorm_base_path, scorm_output_dir)

            shutil.copy(pdf_path, os.path.join(scorm_output_dir, "web", "document.pdf"))

            viewer_path = os.path.join(scorm_output_dir, "web", "viewer.html")
            with open(viewer_path, "r", encoding="utf-8") as f:
                viewer_html = f.read()
            viewer_html = viewer_html.replace("file=compressed.tracemonkey-pldi-09.pdf", "file=document.pdf")
            viewer_html = viewer_html.replace("print", "")
            viewer_html = viewer_html.replace("download", "")
            with open(viewer_path, "w", encoding="utf-8") as f:
                f.write(viewer_html)

            scorm_js_path = os.path.join(scorm_output_dir, "scorm.js")
            with open(scorm_js_path, "w") as f:
                f.write(f"""
// Placeholder SCORM logic
var required_time = {min_seconds};
var required_pages = {num_pages if 'pages' in completion_criteria else 0};
function checkCompletion(timeSpent, pagesViewed) {{
  if ({'true' if 'temps' in completion_criteria else 'false'} && timeSpent < required_time) return false;
  if ({'true' if 'pages' in completion_criteria else 'false'} && pagesViewed < required_pages) return false;
  return true;
}}
                """)

            manifest_path = os.path.join(scorm_output_dir, "imsmanifest.xml")
            with open(manifest_path, "w") as f:
                f.write(f"""
<manifest identifier="{module_title.replace(' ', '_')}">
  <organizations>
    <organization>
      <title>{module_title}</title>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res1" type="webcontent" href="web/viewer.html">
      <file href="web/viewer.html"/>
      <file href="web/document.pdf"/>
      <file href="scorm.js"/>
    </resource>
  </resources>
</manifest>
                """)

            zip_path = os.path.join(tmpdir, f"{module_title.replace(' ', '_')}.zip")
            shutil.make_archive(base_name=zip_path[:-4], format='zip', root_dir=scorm_output_dir)

            with open(zip_path, "rb") as f:
                st.download_button(
                    label="Télécharger le package SCORM",
                    data=f,
                    file_name=os.path.basename(zip_path),
                    mime="application/zip"
                )
