import streamlit as st
import xml.etree.ElementTree as ET
from xml.dom import minidom
from io import BytesIO, StringIO

def prettify_xml(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def convert_xliff_1_2_to_2_1_string(xliff_1_2_content):
    # Parser le XML depuis string
    root = ET.fromstring(xliff_1_2_content)

    ns = {'xliff12': 'urn:oasis:names:tc:xliff:document:1.2'}

    # Créer racine XLIFF 2.1
    xliff21 = ET.Element('xliff', {
        'version': '2.1',
        'xmlns': 'urn:oasis:names:tc:xliff:document:2.1'
    })

    file_elem = root.find('xliff12:file', ns)
    if file_elem is None:
        raise ValueError("Le fichier XLIFF 1.2 ne contient pas de <file>")

    src_lang = file_elem.get('source-language', '')
    trg_lang = file_elem.get('target-language', '')

    new_file = ET.SubElement(xliff21, 'file', {
        'id': 'f1',
        'srcLang': src_lang,
        'trgLang': trg_lang
    })

    body = file_elem.find('xliff12:body', ns)
    if body is None:
        raise ValueError("Le fichier XLIFF 1.2 ne contient pas de <body>")

    for i, trans_unit in enumerate(body.findall('xliff12:trans-unit', ns)):
        unit_id = trans_unit.get('id', f'u{i+1}')
        source_text = trans_unit.findtext('xliff12:source', '', ns)
        target_text = trans_unit.findtext('xliff12:target', '', ns)

        unit = ET.SubElement(new_file, 'unit', {'id': unit_id})
        segment = ET.SubElement(unit, 'segment')
        source = ET.SubElement(segment, 'source')
        source.text = source_text

        if target_text:
            target = ET.SubElement(segment, 'target')
            target.text = target_text

    return prettify_xml(xliff21)

# Streamlit app

st.title("Convertisseur XLIFF 1.2 → 2.1")

uploaded_file = st.file_uploader("Importer un fichier XLIFF 1.2", type=["xliff", "xml"])

if uploaded_file:
    try:
        content = uploaded_file.read().decode('utf-8')
        converted_xliff = convert_xliff_1_2_to_2_1_string(content)

        st.success("Conversion réussie !")

        # Affichage du contenu converti (optionnel)
        with st.expander("Voir le fichier converti"):
            st.code(converted_xliff, language='xml')

        # Préparer téléchargement
        converted_bytes = converted_xliff.encode('utf-8')
        st.download_button(
            label="Télécharger le fichier XLIFF 2.1",
            data=converted_bytes,
            file_name="converted_2.1.xliff",
            mime="application/xml"
        )

    except Exception as e:
        st.error(f"Erreur lors de la conversion : {e}")
