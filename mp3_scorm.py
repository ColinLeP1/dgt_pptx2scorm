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

  canvas {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100% !important;
    height: 100% !important;
    pointer-events: none;
    z-index: 5;  /* plus bas que les sous-titres */
    mix-blend-mode: screen;
  }}

  .plyr__captions {{
    position: absolute;
    bottom: 10%;
    width: 100%;
    z-index: 10; /* au-dessus du canvas */
    background: rgba(0, 0, 0, 0.7); /* fond noir semi-transparent */
    padding: 5px 10px;
    border-radius: 5px;
    font-size: 1.2em;
    line-height: 1.4;
  }}

  .plyr__caption {{
    color: white;
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

    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.clientWidth * window.devicePixelRatio;
    canvas.height = canvas.clientHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    let audioContext;
    let analyser;
    let source;

    function setupAudio() {{
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      source = audioContext.createMediaElementSource(audio);
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyser.connect(audioContext.destination);
    }}

    function draw() {{
      requestAnimationFrame(draw);
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const barWidth = canvas.width / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {{
        const barHeight = dataArray[i] / 255 * canvas.height;
        const red = Math.min(255, barHeight + 100);
        const green = Math.min(255, 250 * (i / bufferLength));
        const blue = 50;
        ctx.fillStyle = `rgb(${{red}},${{green}},${{blue}})`;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 1;
      }}
    }}

    audio.addEventListener('play', () => {{
      if (!audioContext) {{
        setupAudio();
        draw();
      }}
      if (audioContext.state === 'suspended') {{
        audioContext.resume();
      }}
    }});
  </script>
</body>
</html>'''

    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    manifest_xml = create_scorm_manifest(version, scorm_title, mp3_filename, subtitle_filenames)
    with open(os.path.join(output_dir, 'imsmanifest.xml'), 'w', encoding='utf-8') as f:
        f.write(manifest_xml)

# Interface utilisateur Streamlit
st.title("Convertisseur MP3 → SCORM avec Spectre Audio et Sous-titres")

uploaded_file = st.file_uploader("Choisissez un fichier MP3", type=["mp3"])
add_subtitles = st.checkbox("Ajouter des sous-titres")

languages = [(lang.alpha_2, lang.name) for lang in pycountry.languages if hasattr(lang, 'alpha_2')]
languages = sorted(languages, key=lambda x: x[1])
language_options = [f"{name} ({code})" for code, name in languages]
code_map = {f"{name} ({code})": code for code, name in languages}

selected_languages = []
subtitle_files_dict = {}

if add_subtitles:
    st.markdown("### Sélection des langues pour les sous-titres")
    selected_labels = st.multiselect(
        "Choisissez les langues des sous-titres à importer :",
        options=language_options,
        default=[],
        help="Tapez pour rechercher une langue"
    )
    selected_languages = [code_map[label] for label in selected_labels]

    for lang_code in selected_languages:
        subtitle_file = st.file_uploader(
            f"Fichier de sous-titres pour {lang_code}",
            type=["srt", "vtt"],
            key=f"sub_{lang_code}"
        )
        if subtitle_file:
            subtitle_files_dict[lang_code] = subtitle_file

scorm_12 = st.checkbox("SCORM 1.2")
scorm_2004 = st.checkbox("SCORM 2004")

scorm_title = st.text_input("Titre du package SCORM :", value=uploaded_file.name.rsplit(".", 1)[0] if uploaded_file else "Mon Cours Audio SCORM")

if uploaded_file:
    temp_dir = f"temp_scorm_{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)

    mp3_path = os.path.join(temp_dir, uploaded_file.name)
    with open(mp3_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    subtitle_paths = []
    for lang_code, file in subtitle_files_dict.items():
        ext = os.path.splitext(file.name)[1].lower()
        if ext == '.srt':
            # Sauvegarder le srt
            srt_filename = f"sub_{lang_code}.srt"
            srt_path = os.path.join(temp_dir, srt_filename)
            with open(srt_path, "wb") as f:
                f.write(file.getbuffer())
            # Convertir en vtt
            vtt_filename = f"sub_{lang_code}.vtt"
            vtt_path = os.path.join(temp_dir, vtt_filename)
            srt_to_vtt(srt_path, vtt_path)
            subtitle_paths.append(vtt_path)  # On utilise le .vtt converti
        else:
            # Pas besoin de conversion, on copie directement
            filename = f"sub_{lang_code}{ext}"
            path = os.path.join(temp_dir, filename)
            with open(path, "wb") as f:
                f.write(file.getbuffer())
            subtitle_paths.append(path)
    completion_rate = st.slider(
        "Taux de complétion requis (%) pour valider l'audio :",
        min_value=10,
        max_value=100,
        value=80,
        step=5,
        help="L'audio doit être écouté au moins à ce pourcentage pour être considéré comme complété."
    )
    
    if st.button("Créer le package SCORM"):
        if not (scorm_12 or scorm_2004):
            st.error("Veuillez sélectionner au moins une version SCORM (1.2 ou 2004).")
        else:
            selected_version = "1.2" if scorm_12 else "2004"
            output_dir = f"scorm_output_{uuid.uuid4()}"
            create_scorm_package(mp3_path, subtitle_paths, output_dir, selected_version, scorm_title, completion_rate)
            shutil.make_archive(output_dir, 'zip', output_dir)
            with open(f"{output_dir}.zip", "rb") as f:
                st.download_button("Télécharger le package SCORM", f, file_name=f"{scorm_title}.zip")

            # Nettoyage
            shutil.rmtree(temp_dir)
            shutil.rmtree(output_dir)
