import streamlit as st
import re
import os
import tempfile
import shutil
import zipfile

st.set_page_config(page_title="Générateur SCORM PDF", layout="centered")
st.title("📦 Générateur de SCORM à partir d’un PDF")

uploaded_file = st.file_uploader("Téléversez un fichier PDF", type="pdf")

# Définir le titre et le nom du fichier par défaut, unique pour les deux
default_title = uploaded_file.name.replace(".pdf", "") if uploaded_file else "Module_SCORM"
scorm_title = st.text_input("Titre du module SCORM (sera aussi utilisé pour le nom du fichier ZIP)", value=default_title)
scorm_filename = re.sub(r"[^\w\-]", "_", scorm_title)  # Généré automatiquement, pas de champ utilisateur

# Critères de validation
validation_choice = st.selectbox(
    "Critère(s) de validation",
    options=[
        "Lecture de toutes les pages uniquement",
        "Temps écoulé uniquement",
        "Lecture de toutes les pages ET temps écoulé"
    ]
)

# Timer de visualisation (affiché uniquement si le timer est dans le critère)
show_timer = validation_choice in ["Temps écoulé uniquement", "Lecture de toutes les pages ET temps écoulé"]
if show_timer:
    time_str = st.text_input("Temps de visualisation requis (HH:MM:SS)", "00:05:00")
else:
    time_str = "00:05:00"  # valeur par défaut pour la génération, même si non utilisée

def parse_hms(hms_str):
    match = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", hms_str)
    if not match:
        return None
    h, m, s = map(int, match.groups())
    return h * 3600 + m * 60 + s

seconds_required = parse_hms(time_str) if show_timer else 0
if show_timer:
    if seconds_required is None:
        st.error("⛔ Format invalide. Utilisez HH:MM:SS.")
    elif seconds_required > 86400:
        st.error("⛔ Le temps ne doit pas dépasser 24h.")

# Choix version SCORM (un seul checkbox sélectionné à la fois, affichage dynamique)
st.subheader("Version SCORM")

def scorm_12_callback():
    if st.session_state.scorm_12:
        st.session_state.scorm_2004 = False

def scorm_2004_callback():
    if st.session_state.scorm_2004:
        # Ne désactive pas le checkbox scorm_12, pour que l'utilisateur puisse modifier
        pass

if 'scorm_12' not in st.session_state:
    st.session_state.scorm_12 = False
if 'scorm_2004' not in st.session_state:
    st.session_state.scorm_2004 = False

scorm_12 = st.checkbox("SCORM 1.2", key="scorm_12", on_change=scorm_12_callback)
scorm_2004 = st.checkbox("SCORM 2004", key="scorm_2004", on_change=scorm_2004_callback)

if scorm_12 and scorm_2004:
    st.error("❌ Veuillez sélectionner une seule version SCORM.")
elif not scorm_12 and not scorm_2004:
    st.info("ℹ️ Veuillez choisir une version de SCORM.")

# Options pour le PDF : imprimable et téléchargeable
st.subheader("Options du PDF")
allow_print = st.checkbox("Autoriser l'impression du PDF", value=False)
allow_download = st.checkbox("Autoriser le téléchargement du PDF", value=False)

# Affichage du critère de validation au-dessus du PDF (à intégrer dans index.html)
validation_display_text = {
    "Lecture de toutes les pages uniquement": "Critère de validation : Lecture de toutes les pages uniquement.",
    "Temps écoulé uniquement": f"Critère de validation : Temps écoulé ({time_str}).",
    "Lecture de toutes les pages ET temps écoulé": f"Critère de validation : Lecture de toutes les pages ET temps écoulé ({time_str})."
}

if uploaded_file and (scorm_12 != scorm_2004) and (not show_timer or (seconds_required is not None and seconds_required <= 86400)):
    if st.button("📁 Générer le SCORM"):
        if not uploaded_file:
            st.error("Veuillez téléverser un fichier PDF.")
        elif show_timer and (seconds_required is None or seconds_required > 86400):
            st.error("Le timer est invalide.")
        elif scorm_12 == scorm_2004:
            st.error("Veuillez choisir une seule version SCORM.")
        else:
            scorm_version = "1.2" if scorm_12 else "2004"
            with st.spinner("📦 Création du package SCORM..."):
                temp_dir = tempfile.mkdtemp()
                pdf_filename = uploaded_file.name
                pdf_path = os.path.join(temp_dir, pdf_filename)

                # Sauvegarder le fichier PDF
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.read())

                # Création du fichier viewer.js avec modification selon options impression/téléchargement
                viewer_js_content = f"""// viewer.js - Configuration pour contrôle des boutons
document.addEventListener('DOMContentLoaded', function() {{
  // Ligne 84: impression
  {'// ' if not allow_print else ''}document.getElementById('print').addEventListener('click', function(e) {{
    e.preventDefault();
  }});
  // Ligne 86: téléchargement
  {'// ' if not allow_download else ''}document.getElementById('download').addEventListener('click', function(e) {{
    e.preventDefault();
  }});
}});
"""
                with open(os.path.join(temp_dir, "viewer.js"), "w", encoding="utf-8") as f:
                    f.write(viewer_js_content)

                # HTML avec lecteur PDF + timer + critère validation + inclusion viewer.js
                html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{scorm_title}</title>
  <style>
    body {{ font-family: sans-serif; background: #f8f9fa; padding: 20px; }}
    h1 {{ color: #333; }}
    #validation_criteria {{ font-size: 18px; font-weight: bold; margin-bottom: 15px; color: darkgreen; }}
    #timer {{ font-size: 20px; font-weight: bold; margin-bottom: 15px; color: darkblue; }}
    embed {{ width: 100%; height: 600px; border: 1px solid #ccc; }}
  </style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <div id="validation_criteria">{validation_display_text[validation_choice]}</div>"""

                if show_timer:
                    html_content += f"""
  <div id="timer">Temps restant : {time_str}</div>"""

                html_content += f"""
  <embed src="{pdf_filename}" type="application/pdf" id="pdf_embed" />

  <script src="viewer.js"></script>

  <script>
    {"let remaining = " + str(seconds_required) + ";" if show_timer else ""}
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

    {"updateTimer(); const timer = setInterval(updateTimer, 1000);" if show_timer else ""}
  </script>
</body>
</html>"""

                with open(os.path.join(temp_dir, "index.html"), "w", encoding="utf-8") as f:
                    f.write(html_content)

                # Manifeste SCORM
                with open(os.path.join(temp_dir, "imsmanifest.xml"), "w", encoding="utf-8") as f:
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
      <title>{scorm_title}</title>
      <item identifier="item1" identifierref="res1">
        <title>{scorm_title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res1" type="webcontent" adlcp:scormType="sco" href="index.html">
      <file href="index.html"/>
      <file href="{pdf_filename}"/>
      <file href="viewer.js"/>
    </resource>
  </resources>
</manifest>""")

                # Création du zip
                zip_path = os.path.join(temp_dir, f"{scorm_filename}.zip")
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for folder, _, files in os.walk(temp_dir):
                        for file in files:
                            if file.endswith(".zip"): 
                                continue
                            full_path = os.path.join(folder, file)
                            arcname = os.path.relpath(full_path, temp_dir)
                            zipf.write(full_path, arcname)

                # Proposer le téléchargement
                with open(zip_path, "rb") as f:
                    st.success("✅ SCORM généré avec succès.")
                    st.download_button(
                        label="📥 Télécharger le SCORM",
                        data=f,
                        file_name=f"{scorm_filename}.zip",
                        mime="application/zip"
                    )

                shutil.rmtree(temp_dir)
else:
    if not uploaded_file:
        st.info("Veuillez téléverser un fichier PDF pour commencer.")
    elif scorm_12 == scorm_2004:
        st.info("Veuillez choisir une version SCORM.")
    elif show_timer and (seconds_required is None or seconds_required > 86400):
        st.info("Veuillez corriger le temps requis.")

