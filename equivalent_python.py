import streamlit as st
import re
import os
import tempfile
import shutil
import zipfile

st.set_page_config(page_title="Générateur SCORM PDF", layout="centered")
st.title("📦 Générateur de SCORM à partir d’un PDF")

uploaded_file = st.file_uploader("Téléversez un fichier PDF", type="pdf")

# Définir le titre et le nom du fichier par défaut
default_title = uploaded_file.name.replace(".pdf", "") if uploaded_file else "Module_SCORM"
scorm_title = st.text_input("Titre du module SCORM", value=default_title)
scorm_filename = re.sub(r"[^\w\-]", "_", scorm_title)

# Choix version SCORM (une seule possible)
st.subheader("Version SCORM")
scorm_12 = st.checkbox("SCORM 1.2")
scorm_2004 = st.checkbox("SCORM 2004")

if scorm_12 and scorm_2004:
    st.error("❌ Veuillez sélectionner une seule version SCORM.")
elif not scorm_12 and not scorm_2004:
    st.info("ℹ️ Veuillez choisir une version de SCORM.")

# Critères de validation
validation_criteria = st.selectbox(
    "Critères de validation",
    ["Lecture de toutes les pages", "Temps écoulé", "Lecture + Temps écoulé"]
)

# Timer de visualisation (affiché uniquement si le temps est un critère)
if validation_criteria in ["Temps écoulé", "Lecture + Temps écoulé"]:
    time_str = st.text_input("Temps de visualisation requis (HH:MM:SS)", "00:05:00")
else:
    time_str = None

def parse_hms(hms_str):
    match = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", hms_str)
    if not match:
        return None
    h, m, s = map(int, match.groups())
    return h * 3600 + m * 60 + s

seconds_required = parse_hms(time_str) if time_str else 0
if time_str and seconds_required is None:
    st.error("⛔ Format du temps invalide. Utilisez HH:MM:SS.")
elif seconds_required and seconds_required > 86400:
    st.error("⛔ Le temps ne doit pas dépasser 24h.")

# Autorisations impression / téléchargement
allow_print = st.checkbox("Autoriser l'impression", value=False)
allow_download = st.checkbox("Autoriser le téléchargement", value=False)

# Afficher le critère de validation au-dessus du PDF
st.markdown(f"**Critère de validation choisi :** {validation_criteria}")

if st.button("📁 Générer le SCORM"):
    # Validation avant génération
    if not uploaded_file:
        st.error("Veuillez téléverser un fichier PDF.")
    elif validation_criteria in ["Temps écoulé", "Lecture + Temps écoulé"] and (seconds_required is None or seconds_required > 86400):
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

            # Création de viewer.js avec contrôle impression / téléchargement
            viewer_js_lines = [
                "document.addEventListener('DOMContentLoaded', function() {",
                "  const embed = document.querySelector('embed');",
                "  embed.addEventListener('contextmenu', function(e) {",
                "    e.preventDefault();",
                "  });",
                "",
                "  function blockPrint() {",
                "    window.onbeforeprint = function() {",
                "      alert('L\\'impression est désactivée pour ce document.');",
                "      return false;",
                "    };",
                "  }",
                "",
                "  function blockDownload() {",
                "    document.addEventListener('keydown', function(e) {",
                "      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {",
                "        e.preventDefault();",
                "        alert('Le téléchargement est désactivé.');",
                "      }",
                "      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'p') {",
                "        e.preventDefault();",
                "        alert('L\\'impression est désactivée.');",
                "      }",
                "    });",
                "  }",
                ""
            ]

            line_print = "  blockPrint();"
            line_download = "  blockDownload();"

            # Commente la ligne pour désactiver le blocage si autorisé
            if allow_print:
                line_print = "// " + line_print
            if allow_download:
                line_download = "// " + line_download

            viewer_js_lines.append(line_print)
            viewer_js_lines.append(line_download)
            viewer_js_lines.append("});")

            viewer_js_content = "\n".join(viewer_js_lines)

            with open(os.path.join(temp_dir, "viewer.js"), "w", encoding="utf-8") as f:
                f.write(viewer_js_content)

            # Création de l'index.html avec inclusion de viewer.js
            # Timer affiché uniquement si requis par validation
            timer_html = ""
            if validation_criteria in ["Temps écoulé", "Lecture + Temps écoulé"]:
                timer_html = f'<div id="timer">Temps restant : {time_str}</div>'

            html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{scorm_title}</title>
  <style>
    body {{ font-family: sans-serif; background: #f8f9fa; padding: 20px; }}
    h1 {{ color: #333; }}
    #timer {{ font-size: 20px; font-weight: bold; margin-bottom: 15px; color: darkblue; }}
    embed {{ width: 100%; height: 600px; border: 1px solid #ccc; }}
  </style>
</head>
<body>
  <h1>{scorm_title}</h1>
  {timer_html}
  <embed src="{pdf_filename}" type="application/pdf">
  <script src="viewer.js"></script>

  <script>
    {"let remaining = " + str(seconds_required) + ";" if seconds_required else ""}
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
        if(timerDiv) {{
          timerDiv.textContent = "✅ Temps écoulé - SCORM {scorm_version}";
        }}
        clearInterval(timer);
      }}
    }}

    {"if(remaining > 0) { updateTimer(); var timer = setInterval(updateTimer, 1000); }" if seconds_required else ""}
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
      <file href="viewer.js"/>
      <file href="{pdf_filename}"/>
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
