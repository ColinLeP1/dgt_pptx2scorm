import streamlit as st
import os
import shutil
import uuid
import re

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

def create_scorm_package(video_url, output_dir, version, scorm_title="Mon Cours Vidéo SCORM", completion_rate=80):
    os.makedirs(output_dir, exist_ok=True)

    video_id, provider = extract_video_info(video_url)
    if not video_id or not provider:
        raise ValueError("URL vidéo non supportée. Fournissez une URL YouTube ou Dailymotion valide.")

    html_content = f"""<!DOCTYPE html>
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
    <div class="plyr__video-embed" id="player">
      <iframe
        src="https://www.youtube.com/embed/{video_id}?origin=localhost&iv_load_policy=3&modestbranding=1"
        allowfullscreen
        allowtransparency
        allow="autoplay"
      ></iframe>
    </div>
  </div>
  <script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
  <script>
    console.log('Initialisation du player Plyr');

    const completionRate = {completion_rate};
    const message = document.getElementById('completion-message');
    let completed = false;
    let maxTimeReached = 0;  // temps max atteint (en secondes)
    let seekingBlocked = false;  // flag pour éviter boucle infinie dans seeking

    const player = new Plyr('#player', {{
      type: '{provider}',
      sources: [{{
        src: '{video_id}',
        provider: '{provider}'
      }}],
      controls: ['play', 'progress', 'current-time', 'mute', 'volume', 'fullscreen'],
    }});

    player.on('ready', () => console.log('Player prêt'));
    player.on('error', event => console.error('Erreur du player', event));

    player.on('timeupdate', event => {{
      const currentTime = player.currentTime;
      const duration = player.duration || 0;

      if(currentTime > maxTimeReached) {{
        maxTimeReached = currentTime;
      }}

      if (duration > 0 && !completed && (currentTime / duration) * 100 >= completionRate) {{
        completed = true;
        message.style.display = 'block';
        console.log('Vidéo complétée');
      }}
    }});

    player.on('seeking', event => {{
      if (seekingBlocked) {{
        seekingBlocked = false;
        return;
      }}
      const seekTime = player.currentTime;
      if (seekTime > maxTimeReached) {{
        seekingBlocked = true;
        player.currentTime = maxTimeReached;
        console.log(`Avance bloquée à ${{maxTimeReached.toFixed(2)}}s`);
      }}
    }});
  </script>
</body>
</html>"""



    # Créer dossier js dans le package
    js_dir = os.path.join(output_dir, 'js')
    os.makedirs(js_dir, exist_ok=True)

    # Copier le vrai wrapper.js dans le package
    src_wrapper_path = 'wrapper.js'  # chemin relatif de ton wrapper.js par rapport à app.py
    dst_wrapper_path = os.path.join(js_dir, 'wrapper.js')

    if not os.path.isfile(src_wrapper_path):
        raise FileNotFoundError(f"Le fichier wrapper.js est introuvable au chemin : {src_wrapper_path}")

    shutil.copy(src_wrapper_path, dst_wrapper_path)

    # Écrire le fichier index.html
    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Créer le fichier imsmanifest.xml
    manifest = create_scorm_manifest(version, scorm_title)
    with open(os.path.join(output_dir, 'imsmanifest.xml'), 'w', encoding='utf-8') as f:
        f.write(manifest)

# Streamlit interface
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
