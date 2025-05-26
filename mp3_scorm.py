import streamlit as st
import os
import zipfile
import shutil

# Fonction pour créer le package SCORM
def create_scorm_package(mp3_path, output_dir, scorm_title="Mon Cours Audio SCORM"):

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    mp3_filename = os.path.basename(mp3_path)
    # Copier le mp3 dans output_dir
    shutil.copy(mp3_path, os.path.join(output_dir, mp3_filename))

    # Manifest SCORM 1.2 simple
    imsmanifest = f'''<?xml version="1.0" encoding="UTF-8"?>
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
      <title>{scorm_title}</title>
      <item identifier="ITEM1" identifierref="RES1">
        <title>{scorm_title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES1" type="webcontent" adlcp:scormtype="sco" href="index.html">
      <file href="index.html"/>
      <file href="{mp3_filename}"/>
    </resource>
  </resources>
</manifest>'''

    with open(os.path.join(output_dir, 'imsmanifest.xml'), 'w', encoding='utf-8') as f:
        f.write(imsmanifest)

    # Page HTML avec spectre audio (intégré)
    html_content = f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />
<title>{scorm_title}</title>
<style>
  body {{ font-family: Arial, sans-serif; background-color: #222; color: #eee; padding: 20px; text-align: center; }}
  h1 {{ margin-bottom: 20px; }}
  #audioPlayer {{ display: none; }} /* cacher le lecteur audio */
  canvas {{ border: 1px solid #444; background-color: #000; width: 80%; max-width: 600px; height: 150px; display: block; margin: 0 auto; }}
</style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <audio id="audioPlayer" controls>
    <source src="{mp3_filename}" type="audio/mpeg">
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

      for(let i = 0; i < bufferLength; i++) {{
        const barHeight = dataArray[i] / 255 * canvas.height;
        const red = barHeight + 100;
        const green = 250 * (i / bufferLength);
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


# Streamlit interface
st.title("Convertisseur MP3 → Package SCORM avec Spectre Audio")

uploaded_file = st.file_uploader("Choisissez un fichier MP3", type=["mp3"])

if uploaded_file:
    # Sauvegarder temporairement le mp3 uploadé
    temp_dir = "temp_scorm"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    mp3_path = os.path.join(temp_dir, uploaded_file.name)
    with open(mp3_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.write(f"Fichier MP3 reçu : {uploaded_file.name}")

    if st.button("Générer le package SCORM"):
        output_dir = os.path.join(temp_dir, "scorm_package")
        create_scorm_package(mp3_path, output_dir)

        # Zipper le package SCORM
        zip_path = os.path.join(temp_dir, "scorm_package.zip")
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
                file_name="scorm_package.zip",
                mime="application/zip"
            )
