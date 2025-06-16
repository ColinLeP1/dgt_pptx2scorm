import streamlit as st

# --- Configuration de la page ---
st.set_page_config(page_title="Créateur de Quizz", layout="centered")

st.title("📝 Créateur de Quizz")

# --- Informations générales du quizz ---
st.header("Informations générales")

quiz_title = st.text_input("Titre du quizz")
quiz_description = st.text_area("Description du quizz")

uploaded_image = st.file_uploader("Importer une image pour illustrer le quizz", type=["png", "jpg", "jpeg"])

if uploaded_image:
    st.image(uploaded_image, use_column_width=True)

st.divider()

# --- Création des questions ---
st.header("Ajouter une question")

question_type = st.selectbox("Type de question", ["Vrai / Faux", "QCU (Choix Unique)", "QCM (Choix Multiples)"])
question_statement = st.text_area("Énoncé de la question")

if question_type == "Vrai / Faux":
    correct_answer = st.radio("Réponse correcte", ["Vrai", "Faux"])

elif question_type == "QCU (Choix Unique)":
    options = []
    num_options = st.number_input("Nombre de choix", min_value=2, max_value=6, step=1, value=4)
    for i in range(num_options):
        options.append(st.text_input(f"Choix {i+1}", key=f"qcu_{i}"))
    correct_choice = st.selectbox("Choix correct", options)

elif question_type == "QCM (Choix Multiples)":
    options = []
    correct_choices = []
    num_options = st.number_input("Nombre de choix", min_value=2, max_value=6, step=1, value=4, key="qcm_num")
    for i in range(num_options):
        option_text = st.text_input(f"Choix {i+1}", key=f"qcm_{i}")
        is_correct = st.checkbox(f"Correct ?", key=f"check_{i}")
        options.append(option_text)
        if is_correct:
            correct_choices.append(option_text)

# --- Bouton pour enregistrer la question ---
if st.button("✅ Ajouter cette question au quizz"):
    st.success("Question ajoutée (simulation — stockage non implémenté).")

# --- Bonus : Aperçu du quizz ---
st.divider()
st.subheader("🔍 Aperçu du quizz")
st.markdown(f"### {quiz_title}")
if uploaded_image:
    st.image(uploaded_image, use_column_width=True)
st.markdown(quiz_description)
