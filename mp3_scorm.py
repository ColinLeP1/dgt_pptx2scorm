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
        vtt_file.write("WEBVTT\n\n")  # entête obligatoire VTT

        for line in lines:
            if '-->' in line:
                line = line.replace(',', '.')
            vtt_file.write(line)

# Fonction pour générer le fichier manifest selon la version SCORM
def create_scorm_manifest(version, title, mp3_filename, subtitle_filenames):
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
      <file href="{mp3_filename}"/>{subtitle_entries}
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
      <file href="{mp3_filename}"/>{subtitle_entries}
    </resource>
  </resources>
</manifest>'''

# Fonction principale de création du package SCORM
def create_scorm_package(mp3_path, subtitle_paths, output_dir, version, scorm_title="Mon Cours Audio SCORM", completion_rate=80):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    mp3_filename = os.path.basename(mp3_path)
    shutil.copy(mp3_path, os.path.join(output_dir, mp3_filename))

    subtitle_filenames = []
    if subtitle_paths:
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

  /* Nouveau style canvas centré et taille fixe */
  canvas {{
    display: block;
    margin: 40px auto;
    background-color: black;
    border-radius: 10px;
    width: 80%;
    max-width: 600px;
    height: 50px;
    position: relative;
    z-index: 5;
  }}

  .plyr__captions {{
    position: relative;
    z-index: 10; /* au-dessus du canvas */
  }}

  .plyr__caption {{
    background-color: rgba(0, 0, 0);
    color: white;
    padding: 0.2em 0.4em;
    border-radius: 0.2em;
    font-size: 1.2em;
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
    <source src="{mp3_filename}" type="audio/mp3" />
    {track_elements}
    Your browser does not support the audio element.
  </video>
  <canvas id="canvas"></canvas>
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

  // --- Animation K2000 sur canvas ---
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');

  function resizeCanvas() {{
    canvas.width = canvas.clientWidth * window.devicePixelRatio;
    canvas.height = canvas.clientHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }}
  resizeCanvas();
  window.addEventListener('resize', () => {{
    resizeCanvas();
  }});

  let posX = 0;
  const speed = 4;

  function drawK2000() {{
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    ctx.clearRect(0, 0, width, height);

    const gradient = ctx.createLinearGradient(posX - 100, 0, posX + 100, 0);
    gradient.addColorStop(0, 'rgba(255, 0, 0, 0)');
    gradient.addColorStop(0.5, 'rgba(255, 0, 0, 1)');
    gradient.addColorStop(1, 'rgba(255, 0, 0, 0)');

    ctx.fillStyle = gradient;
    ctx.fillRect(0, height / 3, width, height / 3);

    ctx.fillStyle = 'rgba(255, 0, 0, 0.8)';
    ctx.fillRect(posX, height / 4, 20, height / 2);

    posX += speed;
    if (posX > width + 20) posX = -20;

    requestAnimationFrame(drawK2000);
  }}

  drawK2000();
</script>
</body>
</html>
'''

    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    # Créer un ZIP du dossier output_dir
    zip_filename = os.path.join(output_dir, "scorm_package.zip")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file != "scorm_package.zip":
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, output_dir)
                    zipf.write(full_path, arcname)
    return zip_filename


# --- Streamlit UI ---

st.title("Créateur de package SCORM audio")

uploaded_mp3 = st.file_uploader("Chargez un fichier audio MP3", type=["mp3"])
uploaded_subs = st.file_uploader("Chargez des fichiers de sous-titres (optionnel)", type=["vtt", "srt"], accept_multiple_files=True)
scorm_version = st.selectbox("Version SCORM", ["1.2", "2004 3rd Edition"])
completion_pct = st.slider("Taux de complétion (%) requis", min_value=50, max_value=100, value=80, step=5)
scorm_title = st.text_input("Titre du package SCORM", value="Mon Cours Audio SCORM")

if uploaded_mp3:
    # Sauvegarde fichiers temporaire
    tmp_dir = os.path.join("tmp", str(uuid.uuid4()))
    os.makedirs(tmp_dir, exist_ok=True)
    mp3_path = os.path.join(tmp_dir, uploaded_mp3.name)
    with open(mp3_path, "wb") as f:
        f.write(uploaded_mp3.getbuffer())

    subtitle_paths = []
    if uploaded_subs:
        for sub in uploaded_subs:
            sub_path = os.path.join(tmp_dir, sub.name)
            # Si srt, convertir en vtt
            if sub.name.endswith(".srt"):
                vtt_path = sub_path[:-4] + ".vtt"
                with open(sub_path, "wb") as f:
                    f.write(sub.getbuffer())
                srt_to_vtt(sub_path, vtt_path)
                subtitle_paths.append(vtt_path)
            else:
                with open(sub_path, "wb") as f:
                    f.write(sub.getbuffer())
                subtitle_paths.append(sub_path)

    if st.button("Créer le package SCORM"):
        zip_file = create_scorm_package(mp3_path, subtitle_paths, tmp_dir, scorm_version, scorm_title, completion_pct)
        with open(zip_file, "rb") as f:
            st.download_button("Télécharger le package SCORM", data=f, file_name="scorm_package.zip", mime="application/zip")

        # Nettoyer tmp? (optionnel)
        # shutil.rmtree(tmp_dir)
