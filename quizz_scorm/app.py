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

options = []
correct_answers = []

if question_type == "Vrai / Faux":
    options = ["Vrai", "Faux"]
    for i, opt in enumerate(options):
        is_correct = st.checkbox(f"✔ Réponse correcte : {opt}", key=f"vf_{i}")
        if is_correct:
            correct_answers.append(opt)

elif question_type == "QCU (Choix Unique)":
    num_options = st.number_input("Nombre de choix", min_value=2, max_value=6, value=4, step=1)
    for i in range(num_options):
        opt = st.text_input(f"Choix {i+1}", key=f"qcu_opt_{i}")
        if opt:
            options.append(opt)
    st.markdown("Cochez **une seule** bonne réponse :")
    for i, opt in enumerate(options):
        is_correct = st.checkbox(f"✔ Réponse correcte : {opt}", key=f"qcu_check_{i}")
        if is_correct:
            correct_answers.append(opt)

elif question_type == "QCM (Choix Multiples)":
    num_options = st.number_input("Nombre de choix", min_value=2, max_value=6, value=4, step=1)
    for i in range(num_options):
        opt = st.text_input(f"Choix {i+1}", key=f"qcm_opt_{i}")
        if opt:
            options.append(opt)
    st.markdown("Cochez les bonnes réponses :")
    for i, opt in enumerate(options):
        is_correct = st.checkbox(f"✔ Réponse correcte : {opt}", key=f"qcm_check_{i}")
        if is_correct:
            correct_answers.append(opt)

# --- Validation ---
if st.button("✅ Ajouter cette question au quizz"):
    if not question_statement:
        st.warning("Veuillez saisir l'énoncé de la question.")
    elif not options:
        st.warning("Veuillez saisir au moins deux choix.")
    elif not correct_answers:
        st.warning("Veuillez cocher au moins une bonne réponse.")
    elif question_type == "QCU (Choix Unique)" and len(correct_answers) > 1:
        st.warning("Pour une QCU, veuillez cocher **une seule** bonne réponse.")
    else:
        st.success("✅ Question ajoutée avec succès (simulation).")
        st.write("**Aperçu de la question :**")
        st.markdown(f"**Énoncé :** {question_statement}")
        st.markdown("**Choix :**")
        for opt in options:
            st.markdown(f"- {opt} {'✅' if opt in correct_answers else ''}")
