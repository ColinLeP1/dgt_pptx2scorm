import streamlit as st
import os
import zipfile
import shutil
import uuid
import pycountry

# Fonction pour convertir un fichier .srt en .vtt
def srt_to_vtt(srt_path, vtt_path):
    with open(srt_path, 'r', encoding='utf-8') as srt_file:
        lines = srt_file.readlines()

    with open(vtt_path, 'w', encoding='utf-8') as vtt_file:
        vtt_file.write("WEBVTT\n\n")
        for line in lines:
            if '-->' in line:
                line = line.replace(',', '.')
            vtt_file.write(line)

# Fonction pour générer le fichier manifest
def create_scorm_manifest(version, title, video_filename, subtitle_filenames):
    subtitle_entries = "".join([f'\n      <file href="{fn}"/>' for fn in subtitle_filenames]) if subtitle_filenames else ""

    if version == "1.2":
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="com.example.scorm" version="1.2"
  xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
  xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2
                      imscp_rootv1p1p2.xsd
                      http://www.adlnet.org/xsd/adlcp_rootv1p2
                      adlcp_rootv1p2.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="ORG1">
    <organization identifier="ORG1">
      <title>{title}</title>
      <item identifier="ITEM1" identifierref="RES1">
        <title>{title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES1" type="webcontent" adlcp:scormtype="sco" href="index.html">
      <file href="index.html"/>
      <file href="{video_filename}"/>{subtitle_entries}
    </resource>
  </resources>
</manifest>'''
    else:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="com.example.scorm2004" version="1.0"
  xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
  xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_v1p3"
  xmlns:imsss="http://www.imsglobal.org/xsd/imsss"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsglobal.org/xsd/imscp_v1p1
                      imscp_v1p1.xsd
                      http://www.adlnet.org/xsd/adlcp_v1p3
                      adlcp_v1p3.xsd
                      http://www.imsglobal.org/xsd/imsss
                      imsss_v1p0.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>2004 3rd Edition</schemaversion>
  </metadata>
  <organizations default="ORG1">
    <organization identifier="ORG1">
      <title>{title}</title>
      <item identifier="ITEM1" identifierref="RES1" isvisible="true">
        <title>{title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES1" type="webcontent" adlcp:scormType="sco" href="index.html">
      <file href="index.html"/>
      <file href="{video_filename}"/>{subtitle_entries}
    </resource>
  </resources>
</manifest>'''

# Fonction principale

def create_scorm_package(video_path, subtitle_paths, output_dir, version, scorm_title="Mon Cours Vidéo SCORM", completion_rate=80):
    os.makedirs(output_dir, exist_ok=True)
    video_filename = os.path.basename(video_path)
    shutil.copy(video_path, os.path.join(output_dir, video_filename))

    subtitle_filenames = []
    for path in subtitle_paths:
        filename = os.path.basename(path)
        subtitle_filenames.append(filename)
        shutil.copy(path, os.path.join(output_dir, filename))

    track_elements = "\n    ".join([
        f'<track src="{fn}" kind="subtitles" srclang="{os.path.splitext(fn)[0].split("_")[-1]}" label="{os.path.splitext(fn)[0].split("_")[-1].capitalize()}" />'
        for fn in subtitle_filenames
    ])

    html_content = f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <title>{scorm_title}</title>
  <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
  <style>
  body {{
    font-family: Arial, sans-serif;
    background-color: #222;
    color: #eee;
    padding: 20px;
    text-align: center;
  }}

  .player-container {{
    position: relative;
    width: 80%;
    max-width: 600px;
    margin: 0 auto;
  }}

  video, .plyr {{
    width: 100%;
  }}

  .plyr__captions {{
    position: absolute;
    bottom: 10%;
    width: 100%;
    z-index: 10;
    background-color: rgba(0, 0, 0, 0.7);
    padding: 5px 10px;
    border-radius: 5px;
    text-align: center;
  }}

  .plyr__caption {{
    color: white;
    background: transparent;
    font-size: 1.2em;
    line-height: 1.4;
    white-space: pre-wrap;
    display: inline-block;
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
  <p id="completion-info">Taux de complétion requis pour valider : <strong>{completion_rate}%</strong></p>
  <p id="completion-message">Vous avez atteint le seuil de complétion requis 🎉</p>

  <div class="player-container">
    <video id="player" controls crossorigin>
      <source src="{mp4_filename}" type="audio/mp4" />
      {track_elements}
      Your browser does not support the audio element.
    </video>
  </div>

  <script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
  <script>
    const completionRate = {completion_rate};
    const audio = document.getElementById('player');
    const completionMessage = document.getElementById('completion-message');
    let completed = false;
    let maxPlayed = 0;

    function findAPI(win) {{
      let attempts = 0;
      while (win && !win.API && !win.API_1484_11 && win.parent && win !== win.parent && attempts++ < 10) {{
        win = win.parent;
      }}
      return win.API_1484_11 || win.API || null;
    }}

    function setScormCompleted() {{
      const api = findAPI(window);
      if (!api) {{
        console.warn("SCORM API non trouvée.");
        return;
      }}

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

    audio.addEventListener('timeupdate', () => {{
      if (!audio.duration) return;

      if (audio.currentTime > maxPlayed + 0.75) {{
        audio.currentTime = maxPlayed;
      }} else {{
        maxPlayed = Math.max(maxPlayed, audio.currentTime);
      }}

      const playedPercent = (audio.currentTime / audio.duration) * 100;
      if (!completed && playedPercent >= completionRate) {{
        completed = true;
        completionMessage.style.display = 'block';
        setScormCompleted();
      }}
    }});

    const plyrPlayer = new Plyr('#player', {{
      captions: {{ active: true, update: true, language: 'auto' }},
    }});
  </script>
</body>
</html>'''


    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    manifest = create_scorm_manifest(version, scorm_title, video_filename, subtitle_filenames)
    with open(os.path.join(output_dir, 'imsmanifest.xml'), 'w', encoding='utf-8') as f:
        f.write(manifest)

# --- Interface utilisateur Streamlit ---

st.title("Convertisseur Vidéo MP4 → SCORM avec Sous-titres")

uploaded_file = st.file_uploader("Vidéo MP4", type=["mp4"])
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

scorm_12 = st.checkbox("SCORM 1.2")
scorm_2004 = st.checkbox("SCORM 2004")

scorm_title = st.text_input("Titre SCORM :", value=uploaded_file.name.rsplit(".", 1)[0] if uploaded_file else "Mon Cours Vidéo SCORM")

if uploaded_file:
    temp_dir = f"temp_scorm_{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)
    video_path = os.path.join(temp_dir, uploaded_file.name)
    with open(video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    subtitle_paths = []
    for lang_code, file in subtitle_files_dict.items():
        ext = os.path.splitext(file.name)[1].lower()
        if ext == '.srt':
            srt_path = os.path.join(temp_dir, f"sub_{lang_code}.srt")
            vtt_path = os.path.join(temp_dir, f"sub_{lang_code}.vtt")
            with open(srt_path, "wb") as f: f.write(file.getbuffer())
            srt_to_vtt(srt_path, vtt_path)
            subtitle_paths.append(vtt_path)
        else:
            path = os.path.join(temp_dir, f"sub_{lang_code}{ext}")
            with open(path, "wb") as f: f.write(file.getbuffer())
            subtitle_paths.append(path)

    completion_rate = st.slider("Taux de complétion requis (%) :", 10, 100, 80, step=5)

    if st.button("Créer le package SCORM"):
        if not (scorm_12 or scorm_2004):
            st.error("Choisissez une version SCORM.")
        else:
            version = "1.2" if scorm_12 else "2004"
            output_dir = f"scorm_output_{uuid.uuid4()}"
            create_scorm_package(video_path, subtitle_paths, output_dir, version, scorm_title, completion_rate)
            shutil.make_archive(output_dir, 'zip', output_dir)
            with open(f"{output_dir}.zip", "rb") as f:
                st.download_button("Télécharger le package SCORM", f, file_name=f"{scorm_title}.zip")
            shutil.rmtree(temp_dir)
            shutil.rmtree(output_dir)
