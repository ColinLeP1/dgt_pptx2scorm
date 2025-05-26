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
</style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <audio id="audioPlayer" controls>
    <source src="{mp3_filename}" type="audio/mpeg">
    {track_elements}
    Votre navigateur ne supporte pas la lecture audio.
  </audio>
  <canvas id="canvas"></canvas>
  <div id="subtitle"></div>
  <script>
    const audio = document.getElementById('audioPlayer');
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

    const subtitleDiv = document.getElementById('subtitle');

    function animate() {{
      if (!audioContext) return;
      draw();
      requestAnimationFrame(animate);
    }}

    audio.addEventListener('play', () => {{
      if (!audioContext) {{
        setupAudio();
        animate();
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

# -------------------- Ajout pycountry + drapeaux --------------------

# Fonction pour convertir un code pays ISO alpha-2 en emoji drapeau
def country_code_to_emoji(country_code):
    if len(country_code) != 2:
        return ""
    OFFSET = 127397
    return chr(ord(country_code[0].upper()) + OFFSET) + chr(ord(country_code[1].upper()) + OFFSET)

# Génère la liste complète des langues avec un drapeau quand possible
def get_languages_with_flags():
    languages = []
    for lang in pycountry.languages:
        if hasattr(lang, 'alpha_2'):
            lang_code = lang.alpha_2
            lang_name = lang.name
            # On associe certaines langues majeures à un pays pour afficher un drapeau
            mapping = {
                'en': 'GB',
                'fr': 'FR',
                'es': 'ES',
                'de': 'DE',
                'it': 'IT',
                'pt': 'PT',
                'nl': 'NL',
                'zh': 'CN',
                'ja': 'JP',
                'ru': 'RU'
            }
            country = mapping.get(lang_code, None)
            flag = country_code_to_emoji(country) if country else ""
            display_label = f"{flag} {lang_name} ({lang_code})"
            languages.append((display_label, lang_code))
    languages.sort(key=lambda x: x[0])
    return languages

# -------------------- Interface Streamlit --------------------

st.title("Convertisseur MP3 → Package SCORM avec Spectre Audio et Sous-titres")

uploaded_file = st.file_uploader("Choisissez un fichier MP3", type=["mp3"])
add_subtitles = st.checkbox("Ajouter des sous-titres")

subtitle_files_dict = {}
selected_languages = []

if add_subtitles:
    st.markdown("### Sélection des langues pour les sous-titres")

    languages_list = get_languages_with_flags()
    label_to_code = {label: code for label, code in languages_list}

    selected_labels = st.multiselect(
        "Choisissez les langues des sous-titres à importer :",
        options=[label for label, code in languages_list],
        default=[],
        help="Tapez pour rechercher une langue"
    )
    selected_languages = [label_to_code[label] for label in selected_labels]

    for lang_code in selected_languages:
        label = next(label for label, code in languages_list if code == lang_code)
        subtitle_file = st.file_uploader(
            f"Fichier de sous-titres pour {label}",
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
