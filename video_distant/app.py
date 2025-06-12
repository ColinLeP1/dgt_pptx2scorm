import streamlit as st
import os
import shutil
import uuid
import pycountry
import requests

# Fonction pour convertir .srt en .vtt
def srt_to_vtt(srt_path, vtt_path):
    with open(srt_path, 'r', encoding='utf-8') as srt_file:
        lines = srt_file.readlines()
    with open(vtt_path, 'w', encoding='utf-8') as vtt_file:
        vtt_file.write("WEBVTT\n\n")
        for line in lines:
            if '-->' in line:
                line = line.replace(',', '.')
            vtt_file.write(line)

# Fonction pour générer le manifeste SCORM
def create_scorm_manifest(version, title, video_url, subtitle_filenames):
    subtitle_entries = "".join([f'\n      <file href="{fn}"/>' for fn in subtitle_filenames]) if subtitle_filenames else ""
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
    <schemaversion>{version}</schemaversion>
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
      <file href="index.html"/>{subtitle_entries}
    </resource>
  </resources>
</manifest>'''

# Fonction pour créer le SCORM
def create_scorm_package(video_url, subtitle_paths, output_dir, version, scorm_title="Mon Cours Vidéo SCORM", completion_rate=80):
    os.makedirs(output_dir, exist_ok=True)

    subtitle_filenames = []
    for path in subtitle_paths:
        filename = os.path.basename(path)
        subtitle_filenames.append(filename)
        shutil.copy(path, os.path.join(output_dir, filename))

    track_elements = "\n      ".join([
        f'<track src="{fn}" kind="subtitles" srclang="{lang_code}" label="{pycountry.languages.get(alpha_2=lang_code).name if pycountry.languages.get(alpha_2=lang_code) else lang_code}" />'
        for fn in subtitle_filenames
        if (lang_code := os.path.splitext(fn)[0].split("_")[-1])
    ])

    html_content = f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <script src="js/wrapper.js"></script>
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
      width: 80%;
      max-width: 800px;
      margin: auto;
    }}
    video {{
      width: 100%;
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
  <p id="completion-message">🎉 Vous avez terminé la vidéo</p>
  <div class="player-container">
    <video id="player" controls crossorigin>
      <source src="{video_url}" type="video/mp4" />
      {track_elements}
    </video>
  </div>
  <script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
  <script>
    const completionRate = {completion_rate};
    const video = document.getElementById('player');
    const message = document.getElementById('completion-message');
    let maxPlayed = 0;
    let completed = false;

    const player = new Plyr('#player', {{
      captions: {{ active: true, language: 'auto', update: true }},
      speed: {{ selected: 1, options: [0.5, 1, 1.25, 1.5] }}
    }});

    function selectSubtitleTrack() {{
      const lang = (navigator.language || 'en').slice(0, 2);
      const tracks = video.textTracks;
      for (let i = 0; i < tracks.length; i++) {{
        tracks[i].mode = (tracks[i].language === lang) ? 'showing' : 'disabled';
      }}
    }}

    player.on('ready', selectSubtitleTrack);

    video.addEventListener('timeupdate', () => {{
      if (!video.duration) return;
      maxPlayed = Math.max(maxPlayed, video.currentTime);
      if (!completed && (video.currentTime / video.duration) * 100 >= completionRate) {{
        completed = true;
        message.style.display = 'block';
      }}
    }});
  </script>
</body>
</html>
'''
    # Créer les fichiers
    os.makedirs(os.path.join(output_dir, 'js'), exist_ok=True)
    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Copie d’un wrapper.js vide si nécessaire
    with open(os.path.join(output_dir, 'js/wrapper.js'), 'w') as f:
        f.write("// wrapper.js SCORM")

    manifest = create_scorm_manifest(version, scorm_title, video_url, subtitle_filenames)
    with open(os.path.join(output_dir, 'imsmanifest.xml'), 'w', encoding='utf-8') as f:
        f.write(manifest)

# Interface Streamlit

st.title("Convertisseur Vidéo Distante → SCORM")
video_url = st.text_input("URL de la vidéo (MP4 en ligne)", placeholder="https://exemple.com/video.mp4")

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

if video_url:
    temp_dir = f"temp_scorm_{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)

    subtitle_paths = []
    for lang_code, file in subtitle_files_dict.items():
        ext = os.path.splitext(file.name)[1].lower()
        basename = os.path.splitext(file.name)[0]
        new_basename = f"{basename}_{lang_code}" if f"_{lang_code}" not in basename else basename
        filename = f"{new_basename}.vtt"
        local_path = os.path.join(temp_dir, filename)

        with open(local_path if ext == '.vtt' else os.path.join(temp_dir, f"{new_basename}.srt"), "wb") as f:
            f.write(file.getbuffer())

        if ext == '.srt':
            srt_to_vtt(os.path.join(temp_dir, f"{new_basename}.srt"), local_path)

        subtitle_paths.append(local_path)

    completion_rate = st.slider("Taux de complétion requis (%) :", 10, 100, 80, step=5)

    if st.button("Créer le package SCORM"):
        output_dir = f"scorm_output_{uuid.uuid4()}"
        create_scorm_package(video_url, subtitle_paths, output_dir, version, scorm_title, completion_rate)
        shutil.make_archive(output_dir, 'zip', output_dir)
        with open(f"{output_dir}.zip", "rb") as f:
            st.download_button("📦 Télécharger le package SCORM", f, file_name=f"{scorm_title}.zip")
        shutil.rmtree(temp_dir)
        shutil.rmtree(output_dir)
