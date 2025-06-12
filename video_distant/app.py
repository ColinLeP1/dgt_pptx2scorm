import streamlit as st
import os
import shutil
import uuid
import re

# Fonction pour générer le manifeste SCORM
def create_scorm_manifest(version, title):
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
      <file href="index.html"/>
    </resource>
  </resources>
</manifest>'''

# Fonction pour extraire l'ID vidéo et provider YouTube/Dailymotion
def extract_video_info(url):
    url = url.strip()
    if "youtube.com/watch" in url or "youtu.be/" in url:
        m = re.search(r'(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})', url)
        video_id = m.group(1) if m else None
        return video_id, "youtube"
    elif "dailymotion.com/video" in url:
        m = re.search(r'dailymotion\.com/video/([A-Za-z0-9]+)', url)
        video_id = m.group(1) if m else None
        return video_id, "dailymotion"
    else:
        return None, None

# Fonction pour créer le package SCORM avec Plyr iframe (YouTube/Dailymotion)
def create_scorm_package(video_url, output_dir, version, scorm_title="Mon Cours Vidéo SCORM", completion_rate=80):
    os.makedirs(output_dir, exist_ok=True)

    video_id, provider = extract_video_info(video_url)
    if not video_id or not provider:
        raise ValueError("URL vidéo non supportée. Fournissez une URL YouTube ou Dailymotion valide.")

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
    #player {{
      aspect-ratio: 16 / 9;
      width: 100%;
      max-width: 800px;
      margin: auto;
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
    <div id="player"></div>
  </div>
  <script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
  <script>
    const completionRate = {completion_rate};
    const message = document.getElementById('completion-message');
    let completed = false;

    const player = new Plyr('#player', {{
      type: '{provider}',
      sources: [{{
        src: '{video_id}',
        provider: '{provider}'
      }}],
      controls: ['play', 'progress', 'current-time', 'mute', 'volume', 'fullscreen'],
    }});

    // Plyr ne remonte pas toujours la durée des iframes, on utilise un intervalle simple
    player.on('timeupdate', event => {{
      const currentTime = event.detail.plyr.currentTime;
      const duration = event.detail.plyr.duration || 0;
      if (!completed && duration > 0 && (currentTime / duration) * 100 >= completionRate) {{
        completed = true;
        message.style.display = 'block';
      }}
    }});
  </script>
</body>
</html>'''

    os.makedirs(os.path.join(output_dir, 'js'), exist_ok=True)
    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    with open(os.path.join(output_dir, 'js/wrapper.js'), 'w') as f:
        f.write("// wrapper.js SCORM")

    manifest = create_scorm_manifest(version, scorm_title)
    with open(os.path.join(output_dir, 'imsmanifest.xml'), 'w', encoding='utf-8') as f:
        f.write(manifest)

# Interface Streamlit

st.title("Convertisseur Vidéo Distante → SCORM")
video_url = st.text_input("URL de la vidéo", placeholder="https://exemple.com/video.mp4")

version = st.radio("Version SCORM :", options=["1.2", "2004"])
scorm_title = st.text_input("Titre SCORM :", value="Mon Cours Vidéo SCORM")

if video_url:
    completion_rate = st.slider("Taux de complétion requis (%) :", 10, 100, 80, step=5)

    if st.button("Créer le package SCORM"):
        output_dir = f"scorm_output_{uuid.uuid4()}"
        try:
            create_scorm_package(video_url, output_dir, version, scorm_title, completion_rate)
            shutil.make_archive(output_dir, 'zip', output_dir)
            with open(f"{output_dir}.zip", "rb") as f:
                st.download_button("📦 Télécharger le package SCORM", f, file_name=f"{scorm_title}.zip")
            shutil.rmtree(output_dir)
        except Exception as e:
            st.error(f"Erreur : {e}")
