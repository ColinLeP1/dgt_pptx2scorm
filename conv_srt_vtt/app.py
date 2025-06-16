from srt2vtt import srt_to_vtt
from vtt2srt import vtt_to_srt
import streamlit as st

st.title("Convertisseur SRT <-> VTT")

uploaded_file = st.file_uploader("Chargez un fichier SRT ou VTT", type=["srt", "vtt"])

if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    filename = uploaded_file.name

    if filename.endswith(".srt"):
        st.success("Fichier SRT détecté. Conversion en VTT...")
        output = srt_to_vtt(content)
        output_filename = filename.replace(".srt", ".vtt")

    elif filename.endswith(".vtt"):
        st.success("Fichier VTT détecté. Conversion en SRT...")
        output = vtt_to_srt(content)
        output_filename = filename.replace(".vtt", ".srt")

    else:
        st.error("Format non supporté.")
        output = None

    if output:
        st.download_button(
            label="📥 Télécharger le fichier converti",
            data=output,
            file_name=output_filename,
            mime="text/plain"
        )
