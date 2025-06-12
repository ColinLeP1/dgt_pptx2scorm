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
      {''.join([f'<file href="{res}" />' for res in resource_files])}
    </resource>
  </resources>
</manifest>'''
    return manifest

def create_scorm_package_from_url(video_url, subtitle_paths, output_dir, version, scorm_title="Mon Cours Vidéo SCORM", completion_rate=80):
    os.makedirs(output_dir, exist_ok=True)
    js_folder = os.path.join(output_dir, 'js')
    os.makedirs(js_folder, exist_ok=True)

    # JS Wrapper (minimal)
    wrapper_js = """// wrapper.js placeholder
console.log("SCORM wrapper loaded");
"""
    with open(os.path.join(js_folder, 'wrapper.js'), 'w', encoding='utf-8') as f:
        f.write(wrapper_js)

    # Copier les sous-titres
    subtitle_filenames = []
    for path in subtitle_paths:
        filename = os.path.basename(path)
        subtitle_filenames.append(filename)
        shutil.copy(path, os.path.join(output_dir, filename))

    # HTML player
    track_elements = "\n      ".join([
        f'<track src="{fn}" kind="subtitles" srclang="{lang_code}" label="{pycountry.languages.get(alpha_2=lang_code).name if pycountry.languages.get(alpha_2=lang_code) else lang_code}" />'
        for fn in subtitle_filenames
        if (lang_code := os.path.splitext(fn)[0].split("_")[-1])
    ])

    iframe_url = video_url.replace("watch?v=", "embed/") if "youtube.com" in video_url else video_url

    html_content = f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <script src="js/wrapper.js"></script>
  <title>{scorm_title}</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background-color: #222;
      color: #eee;
      padding: 20px;
      text-align: center;
    }}
    iframe {{
      width: 80%;
      max-width: 800px;
      height: 450px;
      border: none;
    }}
    #completion-message {{
      margin-top: 20px;
      font-weight: bold;
      color: #4caf50;
      display: none;
    }}
  </style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <div>
    <iframe src="{iframe_url}" allowfullscreen></iframe>
  </div>
  <p id="completion-message">Vous avez atteint le seuil de complétion requis 🎉</p>
  <script>
    const completionRate = {completion_rate};
    const completionMessage = document.getElementById('completion-message');
    let duration = 120;
    let completed = false;
    let threshold = (duration * completionRate) / 100;

    setTimeout(() => {{
        if (!completed) {{
            completed = true;
            completionMessage.style.display = 'block';
            const api = window.parent.API || window.parent.API_1484_11;
            if (api) {{
                try {{
                    if (api.SetValue) {{
                        api.SetValue("cmi.completion_status", "completed");
                        api.Commit("");
                    }} else if (api.LMSSetValue) {{
                        api.LMSSetValue("cmi.core.lesson_status", "completed");
                        api.LMSCommit("");
                    }}
                }} catch (e) {{
                    console.error("Erreur SCORM:", e);
                }}
            }}
        }}
    }}, threshold * 1000);
  </script>
</body>
</html>'''

    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    manifest = create_scorm_manifest(version, scorm_title, "index.html", subtitle_filenames)
    with open(os.path.join(output_dir, 'imsmanifest.xml'), 'w', encoding='utf-8') as f:
        f.write(manifest)

# --- Interface Streamlit ---

st.title("Convertisseur Vidéo Distante → SCORM avec Sous-titres")

video_url = st.text_input("URL de la vidéo distante (YouTube, Dailymotion, etc.)", placeholder="https://www.youtube.com/watch?v=...")

add_subtitles = st.checkbox("Ajouter des sous-titres")

languages = [(lang.alpha_2, lang.name) for lang in pycountry.languages if hasattr(lang, 'alpha_2')]
languages = sorted(languages, key=lambda x: x[1])
language_options = [f"{name} ({code})" for code, name in languages]
code_map = {f"{name} ({code})": code for code, name in languages}

selected_languages = []
subtitle_files_dict = {}

if add_subtitles:
    selected_labels = st.multiselect("Langues des sous-titres :", options=language_options)
    selected_languages = [code_map[label] for label in selected_labels]
    for lang_code in selected_languages:
        subtitle_file = st.file_uploader(f"Sous-titre pour {lang_code}", type=["srt", "vtt"], key=f"sub_{lang_code}")
        if subtitle_file:
            subtitle_files_dict[lang_code] = subtitle_file

version = st.radio("Version SCORM :", options=["1.2", "2004"])
scorm_title = st.text_input("Titre SCORM :", value="Mon Cours Vidéo SCORM")
completion_rate = st.slider("Taux de complétion requis (%) :", 10, 100, 80, step=5)

if video_url:
    temp_dir = f"temp_scorm_{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)

    subtitle_paths = []
    for lang_code, file in subtitle_files_dict.items():
        ext = os.path.splitext(file.name)[1].lower()
        basename = os.path.splitext(file.name)[0]
        if f"_{lang_code}" not in basename:
            new_basename = f"{basename}_{lang_code}"
        else:
            new_basename = basename

        filename = f"{new_basename}{ext}"
        path = os.path.join(temp_dir, filename)

        with open(path, "wb") as f:
            f.write(file.getbuffer())

        if ext == '.srt':
            vtt_path = os.path.join(temp_dir, f"{new_basename}.vtt")
            srt_to_vtt(path, vtt_path)
            subtitle_paths.append(vtt_path)
        else:
            subtitle_paths.append(path)

    if st.button("Créer le package SCORM"):
        output_dir = f"scorm_output_{uuid.uuid4()}"
        create_scorm_package_from_url(video_url, subtitle_paths, output_dir, version, scorm_title, completion_rate)
        shutil.make_archive(output_dir, 'zip', output_dir)
        with open(f"{output_dir}.zip", "rb") as f:
            st.download_button("Télécharger le package SCORM", f, file_name=f"{scorm_title}.zip")
        shutil.rmtree(temp_dir)
        shutil.rmtree(output_dir)

