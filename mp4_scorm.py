import streamlit as st
import os
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

# Fonction pour générer le fichier manifest SCORM
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

# Fonction principale pour créer le package SCORM
def create_scorm_package(video_path, subtitle_paths, output_dir, version, scorm_title="Mon Cours Vidéo SCORM", completion_rate=80):
    os.makedirs(output_dir, exist_ok=True)
    
    # Création des sous-dossiers
    video_folder = os.path.join(output_dir, 'video')
    js_folder = os.path.join(output_dir, 'js')
    os.makedirs(video_folder, exist_ok=True)
    os.makedirs(js_folder, exist_ok=True)

    # Copier le wrapper dans le sous-dossier js
    wrapper_src = os.path.join(os.path.dirname(__file__), 'wrapper.js')
    wrapper_dst = os.path.join(js_folder, 'wrapper.js')
    shutil.copyfile(wrapper_src, wrapper_dst)

    # Copier la vidéo dans le sous-dossier vidéo
    video_filename = "video/video.mp4"
    shutil.copy(video_path, os.path.join(output_dir, video_filename))

    # Copier les sous-titres à la racine du package
    subtitle_filenames = []
    for path in subtitle_paths:
        filename = os.path.basename(path)
        subtitle_filenames.append(filename)
        shutil.copy(path, os.path.join(output_dir, filename))

    # Génération des <track> pour les sous-titres
    track_elements = "\n      ".join([
        f'<track src="{fn}" kind="subtitles" srclang="{lang_code}" label="{pycountry.languages.get(alpha_2=lang_code).name if pycountry.languages.get(alpha_2=lang_code) else lang_code}" />'
        for fn in subtitle_filenames
        if (lang_code := os.path.splitext(fn)[0].split("_")[-1])
    ])

    # Génération du HTML
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
    #completion-info {{
      display: none;
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
  <p id="completion-info">Taux de complétion requis atteint : <strong>{completion_rate}%</strong></p>
  <p id="completion-message">Vous avez atteint le seuil de complétion requis 🎉</p>

  <div class="player-container">
    <video id="player" controls crossorigin>
      <source src="{video_filename}" type="video/mp4" />
      {track_elements}
      Votre navigateur ne prend pas en charge la vidéo.
    </video>
  </div>
  <script src="js/wrapper.js"></script>
  <script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
  <script>
    const completionRate = {completion_rate};
    const video = document.getElementById('player');
    const completionMessage = document.getElementById('completion-message');
    let maxPlayed = 0;
    let completed = false;

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

    function selectSubtitleTrack(player) {{
      const userLang = navigator.language || navigator.userLanguage;
      const langCode = userLang ? userLang.slice(0, 2) : null;

      const tracks = player.elements.video.textTracks;
      let selectedTrackIndex = -1;

      for (let i = 0; i < tracks.length; i++) {{
        if (tracks[i].language === langCode) {{
          selectedTrackIndex = i;
          break;
        }}
      }}

      if (selectedTrackIndex === -1) {{
        for (let i = 0; i < tracks.length; i++) {{
          if (tracks[i].language === 'en') {{
            selectedTrackIndex = i;
            break;
          }}
        }}
      }}

      for (let i = 0; i < tracks.length; i++) {{
        tracks[i].mode = (i === selectedTrackIndex) ? 'showing' : 'disabled';
      }}
    }}

    video.addEventListener('timeupdate', () => {{
      if (!video.duration) return;

      if (video.currentTime > maxPlayed + 0.75) {{
        video.currentTime = maxPlayed;
      }} else {{
        maxPlayed = Math.max(maxPlayed, video.currentTime);
      }}

      const playedPercent = (video.currentTime / video.duration) * 100;
      if (!completed && playedPercent >= completionRate) {{
        completed = true;
        document.getElementById('completion-info').style.display = 'block';
        completionMessage.style.display = 'block';
        setScormCompleted();
      }}
    }});

    function initScorm() {{
      try {{
        const api = findAPI(window);
        if (api && api.Initialize) {{
          api.Initialize("");
        }} else if (api && api.LMSInitialize) {{
          api.LMSInitialize("");
        }}
      }} catch (e) {{
        console.warn("Erreur lors de l'initialisation SCORM:", e);
      }}
    }}

    function quitScorm() {{
      try {{
        const api = findAPI(window);
        if (api && api.Terminate) {{
          api.Terminate("");
        }} else if (api && api.LMSFinish) {{
          api.LMSFinish("");
        }}
      }} catch (e) {{
        console.warn("Erreur lors de la fermeture SCORM:", e);
      }}
    }}

    window.addEventListener('load', () => {{
      initScorm();
    }});
    window.onbeforeunload = () => {{
      quitScorm();
    }};

    const plyrPlayer = new Plyr('#player', {{
      speed: {{
        selected: 1,
        options: [0.5, 1, 1.25, 1.5]
      }},
      captions: {{
        active: true,
        update: true,
        language: 'auto'
      }}
    }});

    plyrPlayer.on('ready', () => {{
      selectSubtitleTrack(plyrPlayer);
    }});
  </script>
</body>
</html>
'''

    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Génération du manifeste SCORM
    manifest = create_scorm_manifest(version, scorm_title, video_filename, subtitle_filenames)
    with open(os.path.join(output_dir, 'imsmanifest.xml'), 'w', encoding='utf-8') as f:
        f.write(manifest)


# --- Interface utilisateur Streamlit ---

st.title("Convertisseur Vidéo MP4 → SCORM avec Sous-titres")
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True  # Par défaut sombre

if st.button("Basculer thème sombre/clair"):
    st.session_state.dark_mode = not st.session_state.dark_mode

# Appliquer le style en fonction du thème
dark_css = """
    <style>
    body {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    .stButton > button {
        background-color: #333333;
        color: white;
    }
    </style>
"""

light_css = """
    <style>
    body {
        background-color: #ffffff;
        color: #000000;
    }
    .stButton > button {
        background-color: #dddddd;
        color: black;
    }
    </style>
"""

st.markdown(dark_css if st.session_state.dark_mode else light_css, unsafe_allow_html=True)
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

version = st.radio("Version SCORM :", options=["1.2", "2004"])

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

    completion_rate = st.slider("Taux de complétion requis (%) :", 10, 100, 80, step=5)

    if st.button("Créer le package SCORM"):
        output_dir = f"scorm_output_{uuid.uuid4()}"
        create_scorm_package(video_path, subtitle_paths, output_dir, version, scorm_title, completion_rate)
        shutil.make_archive(output_dir, 'zip', output_dir)
        with open(f"{output_dir}.zip", "rb") as f:
            st.download_button("Télécharger le package SCORM", f, file_name=f"{scorm_title}.zip")
        shutil.rmtree(temp_dir)
        shutil.rmtree(output_dir)
