import streamlit as st
import srt2vtt, vtt2srt  # si les fonctions sont dans srt_vtt.py, adapte selon nom fichier

st.title("Convertisseur SRT <-> VTT")

st.write("Chargez un fichier SRT ou VTT pour le convertir dans l'autre format.")

uploaded_file = st.file_uploader("Choisissez un fichier SRT ou VTT", type=['srt', 'vtt'])

if uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8")
    filename = uploaded_file.name

    if filename.endswith(".srt"):
        st.write("Conversion SRT -> VTT")
        output = srt2vtt(content)
        output_filename = filename.replace(".srt", ".vtt")

    elif filename.endswith(".vtt"):
        st.write("Conversion VTT -> SRT")
        output = vtt2srt(content)
        output_filename = filename.replace(".vtt", ".srt")

    else:
        st.error("Format de fichier non supporté")
        output = None

    if output:
        st.download_button(
            label="Télécharger le fichier converti",
            data=output,
            file_name=output_filename,
            mime="text/plain"
        )
