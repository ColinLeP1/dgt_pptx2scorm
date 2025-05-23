import streamlit as st
import re
import os
import tempfile
import shutil
import zipfile

st.set_page_config(page_title="Générateur SCORM PDF", layout="centered")
st.title("📦 Générateur de SCORM à partir d’un PDF")

uploaded_file = st.file_uploader("Téléversez un fichier PDF", type="pdf")

# Définir le titre et le nom du fichier par défaut
default_title = uploaded_file.name.replace(".pdf", "") if uploaded_file else "Module_SCORM"
scorm_title = st.text_input("Titre du module SCORM (sert aussi de nom de fichier ZIP)", value=default_title)
scorm_filename = re.sub(r"[^\w\-]", "_", scorm_title)

# Choix version SCORM
st.subheader("Version SCORM")
scorm_12 = st.checkbox("SCORM 1.2", key="scorm12")
scorm_2004 = st.checkbox("SCORM 2004", key="scorm2004")

# Gestion du choix unique de version SCORM (affichage dynamique)
if scorm_12 and scorm_2004:
    st.error("❌ Veuillez sélectionner une seule version SCORM.")
    disable_generate = True
elif not scorm_12 and not scorm_2004:
    st.badge("Veuillez sélectionner une version SCORM.")
    disable_generate = True
else : 
    disable_generate = False

# Critère validation
validation_criteria = st.selectbox(
    "Critère(s) de validation",
    options=["Lecture de toutes les pages", "Temps écoulé", "Les deux"]
)

# Timer visible seulement si validation inclut le temps
show_timer = validation_criteria in ["Temps écoulé", "Les deux"]

if show_timer:
    time_str = st.text_input("Temps de visualisation requis (HH:MM:SS)", "00:05:00")
else:
    time_str = "00:00:00"  # On met zéro quand pas utilisé

def parse_hms(hms_str):
    match = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", hms_str)
    if not match:
        return None
    h, m, s = map(int, match.groups())
    return h * 3600 + m * 60 + s

seconds_required = parse_hms(time_str) if show_timer else 0

if show_timer:
    if seconds_required is None:
        st.error("⛔ Format invalide. Utilisez HH:MM:SS.")
    elif seconds_required > 86400:
        st.error("⛔ Le temps ne doit pas dépasser 24h.")

# Options PDF imprimable/téléchargeable
printable = st.checkbox("Rendre le PDF imprimable", value=True)
downloadable = st.checkbox("Rendre le PDF téléchargeable", value=True)

# Affichage critère validation au-dessus du PDF
criteria_text = {
    "Lecture de toutes les pages": "Critère de validation : lecture de toutes les pages",
    "Temps écoulé": "Critère de validation : temps écoulé",
    "Les deux": "Critères de validation : lecture de toutes les pages et temps écoulé"
}
st.markdown(f"**{criteria_text[validation_criteria]}**")

if st.button("📁 Générer le SCORM", disabled=disable_generate):
    if not uploaded_file:
        st.error("Veuillez téléverser un fichier PDF.")
    elif show_timer and (seconds_required is None or seconds_required > 86400):
        st.error("Le timer est invalide.")
    elif scorm_12 == scorm_2004:
        st.error("Veuillez choisir une seule version SCORM.")
    else:
        scorm_version = "1.2" if scorm_12 else "2004"
        with st.spinner("📦 Création du package SCORM..."):

            temp_dir = tempfile.mkdtemp()
            pdf_filename = uploaded_file.name
            pdf_path = os.path.join(temp_dir, pdf_filename)

            # Sauvegarder le fichier PDF
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())

            # Génération du fichier viewer.js avec gestion des boutons imprimer/télécharger
            viewer_js_content = f"""
// viewer.js - contrôle des boutons impression et téléchargement
document.addEventListener("DOMContentLoaded", function() {{
    const printBtn = document.getElementById('print');
    const downloadBtn = document.getElementById('download');

    // Si non imprimable, commenter la ligne 84 (simulé ici en désactivant le bouton)
    {'printBtn.style.display = "none";' if not printable else ''}

    // Si non téléchargeable, commenter la ligne 86 (simulé ici en désactivant le bouton)
    {'downloadBtn.style.display = "none";' if not downloadable else ''}
}});
"""

            with open(os.path.join(temp_dir, "viewer.js"), "w", encoding="utf-8") as f:
                f.write(viewer_js_content)

            # HTML avec lecteur PDF + timer et intégration viewer.js
    if validation_criteria == "lecture":
    # Validation par lecture complète des pages uniquement
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <title>{scorm_title}</title>
  <style>
    body {{ font-family: sans-serif; background: #f8f9fa; padding: 20px; }}
    h1 {{ color: #333; }}
    #validation-status {{ font-weight: bold; margin-bottom: 10px; color: green; }}
    #pdf-container canvas {{ border: 1px solid #ccc; }}
    button {{ margin: 5px; }}
  </style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <div id="validation-status">Pages lues: 0 / 0</div>

  <div id="pdf-container"></div>
  <button id="prev-page">Précédent</button>
  <button id="next-page">Suivant</button>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.15.349/pdf.min.js"></script>
  <script>
    let pdfDoc = null;
    let pagesRead = new Set();
    let totalPages = 0;
    let currentPage = 1;

    const url = '{pdf_filename}';

    const loadingTask = pdfjsLib.getDocument(url);
    loadingTask.promise.then(function(pdf) {{
      pdfDoc = pdf;
      totalPages = pdf.numPages;
      renderPage(1);
      updateCompletion();
    }});

    function renderPage(num) {{
      pdfDoc.getPage(num).then(function(page) {{
        let viewport = page.getViewport({{scale:1.5}});
        let canvas = document.getElementById('pdf-render');
        if (!canvas) {{
          canvas = document.createElement('canvas');
          canvas.id = 'pdf-render';
          document.getElementById('pdf-container').appendChild(canvas);
        }}
        let context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        let renderContext = {{
          canvasContext: context,
          viewport: viewport
        }};
        page.render(renderContext).promise.then(() => {{
          pagesRead.add(num);
          updateCompletion();
        }});
      }});
    }}

    function updateCompletion() {{
      const statusDiv = document.getElementById('validation-status');
      if (pagesRead.size === totalPages) {{
        statusDiv.textContent = "✅ Toutes les pages ont été lues.";
        // Appel possible à l'API SCORM pour notifier la complétion
      }} else {{
        statusDiv.textContent = "Pages lues: " + pagesRead.size + " / " + totalPages;
      }}
    }}

    document.getElementById('next-page').onclick = function() {{
      if (currentPage < totalPages) {{
        currentPage++;
        renderPage(currentPage);
      }}
    }};

    document.getElementById('prev-page').onclick = function() {{
      if (currentPage > 1) {{
        currentPage--;
        renderPage(currentPage);
      }}
    }};
  </script>
</body>
</html>
"""
elif validation_criteria == "timer":
    # Validation par timer uniquement
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <title>{scorm_title}</title>
  <style>
    body {{ font-family: sans-serif; background: #f8f9fa; padding: 20px; }}
    h1 {{ color: #333; }}
    #timer {{ font-size: 20px; font-weight: bold; margin-bottom: 15px; color: darkblue; }}
    embed {{ width: 100%; height: 600px; border: 1px solid #ccc; }}
  </style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <div id="timer">Temps restant : {time_str}</div>
  <embed src="{pdf_filename}" type="application/pdf" {download_attr} {print_attr}>

  <script>
    let remaining = {seconds_required};
    const timerDiv = document.getElementById("timer");

    function updateTimer() {{
      if (remaining > 0) {{
        const h = Math.floor(remaining / 3600);
        const m = Math.floor((remaining % 3600) / 60);
        const s = remaining % 60;
        timerDiv.textContent = "Temps restant : " +
          String(h).padStart(2, '0') + ":" +
          String(m).padStart(2, '0') + ":" +
          String(s).padStart(2, '0');
        remaining--;
      }} else {{
        timerDiv.textContent = "✅ Temps écoulé - SCORM {scorm_version}";
        clearInterval(timer);
      }}
    }}

    updateTimer();
    const timer = setInterval(updateTimer, 1000);
  </script>
</body>
</html>
"""
else:
    # Validation par lecture + timer (both)
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <title>{scorm_title}</title>
  <style>
    body {{ font-family: sans-serif; background: #f8f9fa; padding: 20px; }}
    h1 {{ color: #333; }}
    #validation-status {{ font-weight: bold; margin-bottom: 10px; color: green; }}
    #timer {{ font-size: 20px; font-weight: bold; margin-bottom: 15px; color: darkblue; }}
    #pdf-container canvas {{ border: 1px solid #ccc; }}
    button {{ margin: 5px; }}
  </style>
</head>
<body>
  <h1>{scorm_title}</h1>
  <div id="validation-status">Pages lues: 0 / 0</div>
  <div id="timer">Temps restant : {time_str}</div>

  <div id="pdf-container"></div>
  <button id="prev-page">Précédent</button>
  <button id="next-page">Suivant</button>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.15.349/pdf.min.js"></script>
  <script>
    let pdfDoc = null;
    let pagesRead = new Set();
    let totalPages = 0;
    let currentPage = 1;

    const url = '{pdf_filename}';

    const loadingTask = pdfjsLib.getDocument(url);
    loadingTask.promise.then(function(pdf) {{
      pdfDoc = pdf;
      totalPages = pdf.numPages;
      renderPage(1);
      updateCompletion();
    }});

    function renderPage(num) {{
      pdfDoc.getPage(num).then(function(page) {{
        let viewport = page.getViewport({{scale:1.5}});
        let canvas = document.getElementById('pdf-render');
        if (!canvas) {{
          canvas = document.createElement('canvas');
          canvas.id = 'pdf-render';
          document.getElementById('pdf-container').appendChild(canvas);
        }}
        let context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        let renderContext = {{
          canvasContext: context,
          viewport: viewport
        }};
        page.render(renderContext).promise.then(() => {{
          pagesRead.add(num);
          updateCompletion();
        }});
      }});
    }}

    function updateCompletion() {{
      const statusDiv = document.getElementById('validation-status');
      if (pagesRead.size === totalPages) {{
        statusDiv.textContent = "✅ Toutes les pages ont été lues.";
        // Appel possible à l'API SCORM pour notifier la complétion
      }} else {{
        statusDiv.textContent = "Pages lues: " + pagesRead.size + " / " + totalPages;
      }}
    }}

    document.getElementById('next-page').onclick = function() {{
      if (currentPage < totalPages) {{
        currentPage++;
        renderPage(currentPage);
      }}
    }};

    document.getElementById('prev-page').onclick = function() {{
      if (currentPage > 1) {{
        currentPage--;
        renderPage(currentPage);
      }}
    }};

    let remaining = {seconds_required};
    const timerDiv = document.getElementById("timer");

    function updateTimer() {{
      if (remaining > 0) {{
        const h = Math.floor(remaining / 3600);
        const m = Math.floor((remaining % 3600) / 60);
        const s = remaining % 60;
        timerDiv.textContent = "Temps restant : " +
          String(h).padStart(2, '0') + ":" +
          String(m).padStart(2, '0') + ":" +
          String(s).padStart(2, '0');
        remaining--;
      }} else {{
        timerDiv.textContent = "✅ Temps écoulé - SCORM {scorm_version}";
        clearInterval(timer);
      }}
    }}

    updateTimer();
    const timer = setInterval(updateTimer, 1000);
  </script>
</body>
</html>
"""


            with open(os.path.join(temp_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html_content)

            # Manifeste SCORM
            with open(os.path.join(temp_dir, "imsmanifest.xml"), "w", encoding="utf-8") as f:
                f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="MANIFEST-{scorm_filename}" version="1.0"
  xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
  xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_v1p3"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsglobal.org/xsd/imscp_v1p1
    http://www.imsglobal.org/xsd/imscp_v1p1.xsd
    http://www.adlnet.org/xsd/adlcp_v1p3
    http://www.adlnet.org/xsd/adlcp_v1p3.xsd">
  <organizations default="org1">
    <organization identifier="org1">
      <title>{scorm_title}</title>
      <item identifier="item1" identifierref="res1">
        <title>{scorm_title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res1" type="webcontent" adlcp:scormType="sco" href="index.html">
      <file href="index.html"/>
      <file href="{pdf_filename}"/>
      <file href="viewer.js"/>
    </resource>
  </resources>
</manifest>""")

            # Création du zip
            zip_path = os.path.join(temp_dir, f"{scorm_filename}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for folder, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith(".zip"):
                            continue
                        full_path = os.path.join(folder, file)
                        arcname = os.path.relpath(full_path, temp_dir)
                        zipf.write(full_path, arcname)

            # Proposer le téléchargement
            with open(zip_path, "rb") as f:
                st.success("✅ SCORM généré avec succès.")
                st.download_button(
                    label="📥 Télécharger le SCORM",
                    data=f,
                    file_name=f"{scorm_filename}.zip",
                    mime="application/zip"
                )

            shutil.rmtree(temp_dir)
