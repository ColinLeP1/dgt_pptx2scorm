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

        def create_scorm_package(title, pdf_file, seconds_required, scorm_version, allow_download, allow_print):
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

            # JS pour désactiver clic droit, Ctrl+P, Ctrl+S selon options
            print_js = """
            window.addEventListener('contextmenu', function(e) {
              %s
            });

            window.addEventListener('keydown', function(e) {
              if ((e.ctrlKey || e.metaKey) && (e.key === 'p' || e.key.toLowerCase() === 's')) {
                %s
              }
            });
            """ % (
                "e.preventDefault(); alert('Le clic droit est désactivé pour ce document.');" if not allow_print else "",
                "e.preventDefault(); alert('L\'impression et le téléchargement sont désactivés pour ce document.');" if not allow_print or not allow_download else "",
            )

            # Pas de lien téléchargement en bas de page
            download_link_html = ""

            html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 20px; }}
    #timer {{ font-size: 20px; margin-bottom: 10px; }}
    object, embed {{ width: 100%; height: 600px; border: 1px solid #ccc; }}

    /* Si impression ou téléchargement désactivés, bloquer interaction PDF */
    {'' if allow_print and allow_download else '''
    object, embed {{
      -webkit-user-select: none;
      -moz-user-select: none;
      -ms-user-select: none;
      user-select: none;
      pointer-events: none;
    }}
    '''}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>Veuillez lire le document ci-dessous. Le module sera marqué comme complété après le temps requis.</p>
  <div id="timer">Temps requis : {initial_display}</div>

  <object data="{original_pdf_name}" type="application/pdf">
    <embed src="{original_pdf_name}" type="application/pdf" />
    <p>Votre navigateur ne peut pas afficher le PDF.</p>
  </object>

  {download_link_html}

  <script>
    {print_js}

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
          text = "Temps restant : " + h + "h " + m + "m";
        }} else {{
          const m = Math.floor(remaining / 60);
          const s = remaining % 60;
          text = "Temps restant : " + m.toString().padStart(2, '0') + ":" + s.toString().padStart(2, '0');
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

        with open(os.path.join(temp_dir, "imsmanifest.xml"), "w", encoding="utf-8") as f:
            f.write(generate_manifest(title, original_pdf_name, scorm_version))

        zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
        for root, _, files in os.walk(temp_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, temp_dir)
                zipf.write(full_path, arcname)
        zipf.close()
        shutil.rmtree(temp_dir)

    create_scorm_package(title, pdf_file, total_seconds, scorm_version, allow_download, allow_print)

    st.success("✅ Package SCORM généré avec succès.")
    with open(zip_path, "rb") as f:
        st.download_button("⬇️ Télécharger le package SCORM", data=f, file_name=f"{sanitize_title(title)}.zip")

