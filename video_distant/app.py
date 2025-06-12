import os
import shutil
import uuid
import streamlit as st
import pycountry

def srt_to_vtt(srt_path, vtt_path):
    with open(srt_path, 'r', encoding='utf-8') as srt_file:
        srt_content = srt_file.readlines()

    with open(vtt_path, 'w', encoding='utf-8') as vtt_file:
        vtt_file.write("WEBVTT\n\n")
        for line in srt_content:
            if '-->' in line:
                line = line.replace(',', '.')
            vtt_file.write(line)

def create_scorm_manifest(version, scorm_title, launch_file, resource_files):
    identifier = "VIDEO_SCORM"
    manifest = f'''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{identifier}" version="1.0"
    xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
    xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 
                        imscp_rootv1p1p2.xsd 
                        http://www.adlnet.org/xsd/adlcp_rootv1p2 
                        adlcp_rootv1p2.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>{'1.2' if version == '1.2' else '2004 4th Edition'}</schemaversion>
  </metadata>
  <organizations default="{identifier}_ORG">
    <organization identifier="{identifier}_ORG">
      <title>{scorm_title}</title>
      <item identifier="ITEM1" identifierref="RES1">
        <title>{scorm_title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES1" type="webcontent" adlcp:scormtype="sco" href="{launch_file}">
      <file href="{launch_file}" />
      <file href="js/wrapper.js" />
      <file href="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js" />
      <file href="https://cdn.plyr.io/3.7.8/plyr.css" />
      {''.join([f'<file href="{res}" />' for res in resource_files])}
    </resource>
  </resources>
</manifest>'''
    return manifest

def create_scorm_package_with_plyr(video_url, subtitle_paths, output_dir, version, scorm_title="Mon Cours Vidéo SCORM", completion_rate=80):
    os.makedirs(output_dir, exist_ok=True)
    js_folder = os.path.join(output_dir, 'js')
    os.makedirs(js_folder, exist_ok=True)

    # JS Wrapper
    wrapper_js = """console.log("SCORM wrapper loaded");"""
    with open(os.path.join(js_folder, 'wrapper.js'), 'w', encoding='utf-8') as f:
        f.write(wrapper_js)

    # Sous-titres
    subtitle_filenames = []
    track_elements = ""
    for path in subtitle_paths:
        filename = os.path.basename(path)
        lang_code = os.path.splitext(filename)[0].split("_")[-1]
        lang_label = pycountry.languages.get(alpha_2=lang_code).name if pycountry.languages.get(alpha_2=lang_code) else lang_code
        subtitle_filenames.append(filename)
        shutil.copy(path, os.path.join(output_dir, filename))
        track_elements += f'        <track kind="subtitles" label="{lang_label}" srclang="{lang_code}" src="{filename}" default>\n'

    # HTML
    html_content = f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <title>{scorm_title}</title>
  <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
  <script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
  <script src="js/wrapper.js"></script>
  <style>
    body {{
      background-color: #111;
      color: #fff;
      font-family: Arial, sans-serif;
      text-align: center;
      padding: 20px;
    }}
    .plyr__video-embed {{
      max-width: 960px;
      margin: auto;
    }}
    #completion-message {{
      margin-top: 20px;
      font-size: 18px;
      display: none;
      color: #4caf50;
    }}
  </style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <div class="plyr__video-embed" id="player">
    <iframe src="{video_url.replace("watch?v=", "embed/")}" allowfullscreen allowtransparency allow="autoplay"></iframe>
  </div>
  <p id="completion-message">🎉 Vous avez atteint le taux de complétion requis.</p>

  <script>
    const player = new Plyr('#player', {{
      youtube: {{
        noCookie: true
      }}
    }});

    const completionRate = {completion_rate};
    const thresholdSeconds = 120 * completionRate / 100;
    const message = document.getElementById("completion-message");
    let completed = false;

    setTimeout(() => {{
      if (!completed) {{
        completed = true;
        message.style.display = "block";
        const api = window.parent.API || window.parent.API_1484_11;
        try {{
          if (api?.SetValue) {{
            api.SetValue("cmi.completion_status", "completed");
            api.Commit("");
          }} else if (api?.LMSSetValue) {{
            api.LMSSetValue("cmi.core.lesson_status", "completed");
            api.LMSCommit("");
          }}
        }} catch (e) {{
          console.error("SCORM error:", e);
        }}
      }}
    }}, thresholdSeconds * 1000);
  </script>
</body>
</html>
'''
    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    manifest = create_scorm_manifest(version, scorm_title, "index.html", subtitle_filenames)
    with open(os.path.join(output_dir, 'imsmanifest.xml'), 'w', encoding='utf-8') as f:
        f.write(manifest)

# --- Streamlit App ---

st.title("🎬 Convertisseur SCORM (Vidéo distante avec Plyr + sous-titres)")

video_url = st.text_input("URL vidéo distante (YouTube, etc.)", placeholder="https://www.youtube.com/watch?v=...")

add_subs = st.checkbox("Ajouter des sous-titres")

languages = sorted([(l.alpha_2, l.name) for l in pycountry.languages if hasattr(l, 'alpha_2')], key=lambda x: x[1])
lang_map = {f"{name} ({code})": code for code, name in languages}
lang_labels = list(lang_map.keys())

selected_langs = []
subtitle_files = {}

if add_subs:
    selected_labels = st.multiselect("Langues disponibles :", lang_labels)
    selected_langs = [lang_map[label] for label in selected_labels]
    for lang in selected_langs:
        file = st.file_uploader(f"Sous-titre {lang} :", type=["srt", "vtt"], key=f"sub_{lang}")
        if file:
            subtitle_files[lang] = file

version = st.radio("Version SCORM :", ["1.2", "2004"])
scorm_title = st.text_input("Titre du package SCORM :", "Vidéo SCORM avec Plyr")
completion_rate = st.slider("Taux de complétion (%) :", 10, 100, 80)

if video_url and st.button("Créer le package SCORM"):
    tmp_dir = f"temp_{uuid.uuid4()}"
    os.makedirs(tmp_dir, exist_ok=True)

    subtitle_paths = []
    for lang, file in subtitle_files.items():
        ext = os.path.splitext(file.name)[1].lower()
        base = os.path.splitext(file.name)[0]
        safe_name = f"{base}_{lang}"
        final_name = f"{safe_name}.vtt" if ext == ".srt" else f"{safe_name}{ext}"
        file_path = os.path.join(tmp_dir, final_name)

        with open(file_path, "wb") as f:
            f.write(file.getbuffer())

        if ext == ".srt":
            vtt_path = os.path.join(tmp_dir, f"{safe_name}.vtt")
            srt_to_vtt(file_path, vtt_path)
            subtitle_paths.append(vtt_path)
        else:
            subtitle_paths.append(file_path)

    out_dir = f"scorm_{uuid.uuid4()}"
    create_scorm_package_with_plyr(video_url, subtitle_paths, out_dir, version, scorm_title, completion_rate)
    zip_path = shutil.make_archive(out_dir, "zip", out_dir)

    with open(zip_path, "rb") as f:
        st.download_button("⬇️ Télécharger le package SCORM", f, file_name=f"{scorm_title}.zip")

    shutil.rmtree(tmp_dir)
    shutil.rmtree(out_dir)
