import streamlit as st
import os
import zipfile
import shutil

# Fonction pour générer le fichier manifest selon la version SCORM
def create_scorm_manifest(version, title, mp3_filename, subtitle_filename=None):
    subtitle_entry = f'\n      <file href="{subtitle_filename}"/>' if subtitle_filename else ""

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
      <file href="{mp3_filename}"/>{subtitle_entry}
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
      <file href="{mp3_filename}"/>{subtitle_entry}
    </resource>
  </resources>
</manifest>'''

# Fonction de création du package SCORM
def create_scorm_package(mp3_path, subtitle_path, output_dir, version, scorm_title="Mon Cours Audio SCORM"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    mp3_filename = os.path.basename(mp3_path)
    shutil.copy(mp3_path, os.path.join(output_dir, mp3_filename))

    subtitle_filename = None
    if subtitle_path:
        subtitle_filename = os.path.basename(subtitle_path)
        shutil.copy(subtitle_path, os.path.join(output_dir, subtitle_filename))

    track_tag = f'<track src="{subtitle_filename}" kind="subtitles" srclang="fr" label="Français">' if subtitle_filename else ""

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
</style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <audio id="audioPlayer" controls>
    <source src="{mp3_filename}" type="audio/mpeg">
    {track_tag}
    Votre navigateur ne supporte pas la lecture audio.
  </audio>
  <canvas id="canvas"></canvas>
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
        ctx.fillStyle = `rgb(${red},${green},${blue})`;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 1;
      }}
    }}

    audio.onplay = () => {{
      if (!audioContext) {{
        setupAudio();
        draw();
      }}
      if (audioContext.state === 'suspended') {{
        audioContext.resume();
      }}
    }};
  </script>
</body>
</html>'''

    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    manifest_xml = create_scorm_manifest(version, scorm_title, mp3_filename, subtitle_filename)
    with open(os.path.join(output_dir, 'imsmanifest.xml'), 'w', encoding='utf-8') as f:
        f.write(manifest_xml)

# Interface utilisateur Streamlit
st.title("Convertisseur MP3 → Package SCORM avec Spectre Audio et Sous-titres")

uploaded_file = st.file_uploader("Choisissez un fichier MP3", type=["mp3"])
add_subtitles = st.checkbox("Ajouter des sous-titres")
subtitle_file = None
if add_subtitles:
    subtitle_file = st.file_uploader("Fichier de sous-titres (SRT ou VTT)", type=["srt", "vtt"])

scorm_12 = st.checkbox("SCORM 1.2")
scorm_2004 = st.checkbox("SCORM 2004")
scorm_title = st.text_input("Titre du package SCORM (nom du fichier ZIP) :", value="Mon Cours Audio SCORM")

if uploaded_file:
    temp_dir = "temp_scorm"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    mp3_path = os.path.join(temp_dir, uploaded_file.name)
    with open(mp3_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    subtitle_path = None
    if subtitle_file:
        subtitle_path = os.path.join(temp_dir, subtitle_file.name)
        with open(subtitle_path, "wb") as f:
            f.write(subtitle_file.getbuffer())

    if st.button("Générer le package SCORM"):
        if (scorm_12 and scorm_2004) or (not scorm_12 and not scorm_2004):
            st.error("Veuillez cocher exactement une version SCORM : soit SCORM 1.2, soit SCORM 2004.")
        else:
            version = "1.2" if scorm_12 else "2004"
            output_dir = os.path.join(temp_dir, "scorm_package")
            create_scorm_package(mp3_path, subtitle_path, output_dir, version, scorm_title)

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
