import streamlit as st
import os
import zipfile
import shutil
import uuid
import pycountry

# Fonction pour générer le fichier manifest selon la version SCORM
def create_scorm_manifest(version, title, mp3_filename, subtitle_filenames):
    subtitle_entries = "".join([f"\n      <file href=\"{fn}\"/>" for fn in subtitle_filenames]) if subtitle_filenames else ""

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

def create_scorm_package(mp3_path, subtitle_paths, output_dir, version, scorm_title="Mon Cours Audio SCORM"):
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
<style>
  body {{ font-family: Arial, sans-serif; background-color: #222; color: #eee; padding: 20px; text-align: center; }}
  h1 {{ margin-bottom: 20px; }}
  #audioPlayer {{ display: inline-block; margin-bottom: 10px; }}
  canvas {{ border: 1px solid #444; background-color: #000; width: 80%; max-width: 600px; height: 150px; display: block; margin: 0 auto; }}
  #subtitle {{ color: white; font-size: 20px; margin-top: 10px; height: 40px; }}
  #ccButton {{
    cursor: pointer;
    background-color: #444;
    color: white;
    border: none;
    padding: 5px 10px;
    margin-left: 10px;
    border-radius: 4px;
  }}
  #ccMenu {{
    display: none;
    position: absolute;
    background-color: #333;
    color: white;
    border: 1px solid #555;
    padding: 5px;
    margin-top: 5px;
    border-radius: 4px;
  }}
  #ccMenu button {{
    background: none;
    border: none;
    color: white;
    padding: 5px 10px;
    width: 100%;
    text-align: left;
    cursor: pointer;
  }}
  #ccMenu button:hover {{
    background-color: #555;
  }}
</style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <audio id="audioPlayer" controls crossorigin="anonymous">
    <source src="{mp3_filename}" type="audio/mpeg">
    {track_elements}
    Votre navigateur ne supporte pas la lecture audio.
  </audio>
  <button id="ccButton">CC</button>
  <div id="ccMenu"></div>
  <canvas id="canvas"></canvas>
  <div id="subtitle"></div>
<script>
  const audio = document.getElementById('audioPlayer');
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');
  const ccButton = document.getElementById('ccButton');
  const ccMenu = document.getElementById('ccMenu');

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

  const subtitleDiv = document.getElementById('subtitle');

  // Affiche sous-titre courant
  function showSubtitle(text) {{
    subtitleDiv.textContent = text || "";
  }}

  // Gestion des sous-titres
  let subtitles = [];
  let currentSubtitleIndex = 0;

  function parseVTT(data) {{
    const pattern = /(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\\n(.+)/g;
    let result;
    const cues = [];
    while ((result = pattern.exec(data)) !== null) {{
      cues.push({{
        start: toSeconds(result[1]),
        end: toSeconds(result[2]),
        text: result[3]
      }});
    }}
    return cues;
  }}

  function toSeconds(time) {{
    const parts = time.split(':');
    return parseFloat(parts[0]) * 3600 + parseFloat(parts[1]) * 60 + parseFloat(parts[2]);
  }}

  function loadSubtitles(track) {{
    fetch(track.src).then(response => response.text()).then(text => {{
      subtitles = parseVTT(text);
      currentSubtitleIndex = 0;
    }});
  }}

  function updateSubtitle() {{
    if (!subtitles.length) {{
      showSubtitle("");
      return;
    }}
    const currentTime = audio.currentTime;
    if (currentSubtitleIndex < subtitles.length) {{
      const cue = subtitles[currentSubtitleIndex];
      if (currentTime >= cue.start && currentTime <= cue.end) {{
        showSubtitle(cue.text);
      }} else if (currentTime > cue.end) {{
        currentSubtitleIndex++;
        updateSubtitle();
      }} else {{
        showSubtitle("");
      }}
    }} else {{
      showSubtitle("");
    }}
  }}

  // Bouton CC : afficher/masquer menu
  ccButton.addEventListener('click', () => {{
    if (ccMenu.style.display === 'block') {{
      ccMenu.style.display = 'none';
    }} else {{
      ccMenu.style.display = 'block';
    }}
  }});

  // Crée les boutons pour les pistes de sous-titres
  function createCCButtons() {{
    const tracks = audio.textTracks;
    ccMenu.innerHTML = '';
    for(let i = 0; i < tracks.length; i++) {{
      const btn = document.createElement('button');
      btn.textContent = tracks[i].label;
      btn.onclick = () => {{
        for(let j = 0; j < tracks.length; j++) {{
          tracks[j].mode = 'disabled';
        }}
        tracks[i].mode = 'showing';
        subtitles = [];
        currentSubtitleIndex = 0;
        loadSubtitles(tracks[i]);
      }};
      ccMenu.appendChild(btn);
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

  audio.addEventListener('timeupdate', updateSubtitle);

  audio.addEventListener('loadedmetadata', () => {{
    createCCButtons();
    // Par défaut désactive tous les sous-titres
    for(let i = 0; i < audio.textTracks.length; i++) {{
      audio.textTracks[i].mode = 'disabled';
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

# Interface Streamlit
st.title("Convertisseur MP3 → Package SCORM avec Spectre Audio et Sous-titres")

uploaded_file = st.file_uploader("Choisissez un fichier MP3", type=["mp3"])
add_subtitles = st.checkbox("Ajouter des sous-titres")

def get_language_label(lang):
    # Format "Pays (pa)" où pa = code langue
    try:
        country = pycountry.countries.get(alpha_2=lang.upper())
        country_name = country.name if country else lang.upper()
    except:
        country_name = lang.upper()
    return f"{country_name} ({lang})"

language_codes = sorted({lang.alpha_2.lower() for lang in pycountry.countries if hasattr(lang, 'alpha_2')})

language_options = [get_language_label(code) for code in language_codes]
label_to_code = {label: label.split('(')[-1][:-1] for label in language_options}

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
    selected_languages = [label_to_code[label] for label in selected_labels]

    for lang_code in selected_languages:
        label = get_language_label(lang_code)
        subtitle_file = st.file_uploader(
            f"Fichier de sous-titres pour {label} ({lang_code.upper()})",
            type=["srt", "vtt"],
            key=f"sub_{lang_code}"
        )
        if subtitle_file:
            subtitle_files_dict[lang_code] = subtitle_file

scorm_12 = st.checkbox("SCORM 1.2")
scorm_2004 = st.checkbox("SCORM 2004")
scorm_title = st.text_input("Titre du package SCORM (nom du fichier ZIP) :", value="Mon Cours Audio SCORM")

if uploaded_file:
    temp_dir = f"temp_scorm_{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)

    mp3_path = os.path.join(temp_dir, uploaded_file.name)
    with open(mp3_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    subtitle_paths = []
    for lang_code, file in subtitle_files_dict.items():
        ext = os.path.splitext(file.name)[1]
        filename = f"sub_{lang_code}{ext}"
        path = os.path.join(temp_dir, filename)
        with open(path, "wb") as f:
            f.write(file.getbuffer())
        subtitle_paths.append(path)

    if st.button("Générer le package SCORM"):
        if (scorm_12 and scorm_2004) or (not scorm_12 and not scorm_2004):
            st.error("Veuillez cocher exactement une version SCORM : soit SCORM 1.2, soit SCORM 2004.")
        else:
            version = "1.2" if scorm_12 else "2004"
            output_dir = os.path.join(temp_dir, "scorm_package")
            create_scorm_package(mp3_path, subtitle_paths, output_dir, version, scorm_title)

            zip_path = os.path.join(temp_dir, f"{scorm_title}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for foldername, subfolders, filenames in os.walk(output_dir):
                    for filename in filenames:
                        filepath = os.path.join(foldername, filename)
                        arcname = os.path.relpath(filepath, output_dir)
                        zipf.write(filepath, arcname)

            with open(zip_path, "rb") as f:
                st.download_button(
                    label="Télécharger le package SCORM",
                    data=f,
                    file_name=f"{scorm_title}.zip",
                    mime="application/zip"
                )
