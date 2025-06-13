import streamlit as st
import urllib.parse
import os

st.set_page_config(page_title="Visualiseur SCORM", layout="wide")
st.title("Visualiseur de documents avec options SCORM")

# Sélection du type de fichier
file_type = st.selectbox("Choisissez le type de fichier à importer :", ["PDF", "DOCX"])

# Sélection de la version SCORM
scorm_version = st.radio("Choisissez la version SCORM :", ["SCORM 1.2", "SCORM 2004"])

st.markdown(f"🧩 Vous avez choisi : **{file_type}** avec **{scorm_version}**")
st.markdown("---")

# Dossier temporaire pour stockage local
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# Upload selon le type choisi
uploaded_file = None
if file_type == "DOCX":
    uploaded_file = st.file_uploader("Importer un fichier Word (.docx)", type=["doc", "docx"])
elif file_type == "PDF":
    uploaded_file = st.file_uploader("Importer un fichier PDF", type=["pdf"])

# Affichage
if uploaded_file is not None:
    file_path = os.path.join(TEMP_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    if file_type == "DOCX":
        st.subheader("Aperçu du fichier Word")
        # En local, view.officeapps.live.com ne peut pas charger un fichier non hébergé publiquement
        st.warning("⚠️ Le visualiseur Word nécessite un fichier hébergé publiquement. Cela ne fonctionnera pas en local.")
        local_url = f"http://localhost:8501/{TEMP_DIR}/{urllib.parse.quote(uploaded_file.name)}"
        office_viewer_url = f"https://view.officeapps.live.com/op/embed.aspx?src={urllib.parse.quote(local_url, safe='')}"
        st.components.v1.iframe(office_viewer_url, height=600, scrolling=True)

    elif file_type == "PDF":
        st.subheader("Aperçu du fichier PDF")
        pdf_html = f"""
        <iframe src="/{TEMP_DIR}/{urllib.parse.quote(uploaded_file.name)}" width="100%" height="600px" type="application/pdf"></iframe>
        """
        st.components.v1.html(pdf_html, height=600)
else:
    st.info(f"Veuillez importer un fichier {file_type}.")
