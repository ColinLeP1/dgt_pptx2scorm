import streamlit as st
import zipfile
import os
import tempfile
import shutil
import re
import uuid

st.set_page_config(page_title="Convertisseur PDF vers SCORM", layout="centered")
st.title("📄 Convertisseur PDF vers SCORM")

pdf_file = st.file_uploader("Téléversez un fichier PDF", type="pdf")
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
elif total_seconds > 86400:
    st.warning("⚠️ Temps supérieur à 24h. Veuillez vérifier.")

def sanitize_title(title: str) -> str:
    return re.sub(r"[^\w\-]", "_", title) or "module"

def generate_manifest(title, pdf_name, scorm_version):
    manifest_id = f"scorm_{uuid.uuid4().hex[:8]}"
    lom_metadata = f"""
    <metadata>
      <schema>ADL SCORM</schema>
      <schemaversion>{scorm_version}</schemaversion>
      <lom xmlns="http://ltsc.ieee.org/xsd/LOM">
        <general>
          <title>
            <string language="fr">{title}</string>
          </title>
          <description>
            <string language="fr">Module PDF avec timer et complétion automatique</string>
          </description>
        </general>
      </lom>
    </metadata>
    """
    manifest = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{manifest_id}" version="1.0"
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
      <file href="{pdf_name}"/>
    </resource>
  </resources>
  {lom_metadata}
</manifest>
"""
    return manifest

default_title = os.path.splitext(pdf_file.name)[0] if pdf_file else ""
title = st.text_input("Titre du module", default_title)
scorm_version = st.selectbox("Version SCORM", ["1.2", "2004"])

allow_download = st.checkbox("Autoriser le téléchargement du PDF", value=True)
allow_print = st.checkbox("Autoriser l'impression du PDF", value=True)

if pdf_file and total_seconds and st.button("Générer le package SCORM"):
    with st.spinner("📦 Génération en cours..."):
        output_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        zip_path = output_zip.name

        def create_scorm_package(title, pdf_file, seconds_required, scorm_version, allow_download, allow_print, zip_path):
            temp_dir = tempfile.mkdtemp()

            original_pdf_name = re.sub(r'[^\w\-.]', '_', pdf_file.name)
            pdf_path = os.path.join(temp_dir, original_pdf_name)

            with open(pdf_path, "wb") as f:
                f.write(pdf_file.read())

            if seconds_required >= 3600:
                h = seconds_required // 3600
                m = (seconds_required % 3600) // 60
                initial_display = f"{h}h {m}m"
            elif seconds_required >= 60:
                m = seconds_required // 60
                s = seconds_required % 60
                initial_display = f"{m}m {s}s" if s > 0 else f"{m}m"
            else:
                initial_display = f"{seconds_required}s"

            js_protection = """
            document.addEventListener('contextmenu', e => e.preventDefault());
            document.addEventListener('keydown', function(e) {
                if ((e.ctrlKey || e.metaKey) && ['p','s'].includes(e.key.toLowerCase())) {
                    e.preventDefault();
                    alert("Impression et téléchargement désactivés.");
                }
            });
            """ if not (allow_download and allow_print) else ""

            html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 20px; }}
    #timer {{ font-size: 20px; margin-bottom: 10px; }}
    object, embed {{ width: 100%; height: 600px; pointer-events: none;
