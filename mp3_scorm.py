import os
import shutil
import zipfile

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

def create_scorm_package(mp3_path, subtitle_paths=None, output_dir="scorm_package", version="1.2", scorm_title=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    mp3_filename = os.path.basename(mp3_path)
    if scorm_title is None:
        scorm_title = os.path.splitext(mp3_filename)[0]  # par défaut : nom fichier audio sans extension

    shutil.copy(mp3_path, os.path.join(output_dir, mp3_filename))

    subtitle_filenames = []
    if subtitle_paths:
        for path in subtitle_paths:
            filename = os.path.basename(path)
            subtitle_filenames.append(filename)
            shutil.copy(path, os.path.join(output_dir, filename))

    # Prépare les balises <track> pour sous-titres
    # Utilise la dernière partie du nom de fichier comme code langue, ex : "fichier_fr.srt" → "fr"
    track_elements = "\n      ".join([
        f'<track kind="subtitles" src="{fn}" srclang="{os.path.splitext(fn)[0].split("_")[-1]}" label="{os.path.splitext(fn)[0].split("_")[-1].capitalize()}" />' 
        for fn in subtitle_filenames
    ])

    html_content = f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />
<title>{scorm_title}</title>
<!-- Plyr CSS -->
<link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
<style>
  body {{
    font-family: Arial, sans-serif;
    background-color: #222;
    color: #eee;
    padding: 20px;
    text-align: center;
  }}
  h1 {{
    margin-bottom: 20px;
  }}
  #player-container {{
    max-width: 600px;
    margin: 0 auto;
  }}
  video.plyr {{
    width: 100%;
    max-width: 600px;
    height: 100px; /* hauteur compacte */
    background-color: black;
  }}
  .plyr__captions {{
    color: white !important;
    font-size: 14px !important;
    text-shadow:
      -1px -1px 0 #000,
      1px -1px 0 #000,
      -1px 1px 0 #000,
      1px 1px 0 #000;
  }}
  #canvas {{
    border: 1px solid #444;
    background-color: #000;
    width: 80%;
    max-width: 600px;
    height: 150px;
    margin: 20px auto;
    display: block;
  }}
</style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <div id="player-container">
    <video id="player" class="plyr" controls crossorigin>
      <source src="{mp3_filename}" type="audio/mpeg" />
      {track_elements}
      Votre navigateur ne supporte pas la lecture vidéo.
    </video>
  </div>

  <canvas id="canvas"></canvas>

  <script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
  <script>
    const player = new Plyr('#player', {{
      captions: {{ active: true, language: 'fr', update: true }},
      controls: ['play', 'progress', 'current-time', 'duration', 'mute', 'volume', 'settings', 'fullscreen', 'captions'],
      settings: ['captions', 'quality', 'speed'],
      autoplay: false,
    }});

    const audio = document.getElementById('player');
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

    print(f"Package SCORM créé dans le dossier : {output_dir}")
