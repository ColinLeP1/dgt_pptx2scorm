import streamlit as st

# Initialisation de session
if "questions" not in st.session_state:
    st.session_state.questions = []
if "question_counter" not in st.session_state:
    st.session_state.question_counter = 0

st.set_page_config(page_title="Créateur de Quizz", layout="centered")
st.title("📝 Créateur de Quizz")

# === 1. Informations générales ===
st.header("Informations générales")

quiz_title = st.text_input("Titre du quizz")
quiz_description = st.text_area("Description du quizz")
uploaded_image = st.file_uploader("Importer une image", type=["png", "jpg", "jpeg"])

if uploaded_image:
    st.image(uploaded_image, use_column_width=True)

st.divider()

# === 2. Création de questions ===
st.header("Créer une nouvelle question")

question_type = st.selectbox("Type de question", ["Vrai / Faux", "QCU", "QCM"])
question_statement = st.text_area("Énoncé de la question")

# Nombre de choix
num_options = 2 if question_type == "Vrai / Faux" else st.number_input("Nombre de réponses", min_value=2, max_value=6, value=4, step=1)

# Options avec checkboxes sur la même ligne
st.markdown("**Choix et bonnes réponses :**")
options = []
correct_answers = []

cols = st.columns(2)
for i in range(int(num_options)):
    col1, col2 = st.columns([4, 1])
    with col1:
        opt = st.text_input(f"Réponse {i+1}", key=f"opt_{st.session_state.question_counter}_{i}")
    with col2:
        is_correct = st.checkbox("✔", key=f"chk_{st.session_state.question_counter}_{i}")
    if opt:
        options.append(opt)
        if is_correct:
            correct_answers.append(opt)

# === 3. Ajouter la question ===
if st.button("✅ Ajouter cette question"):
    if not question_statement or len(options) < 2 or not correct_answers:
        st.warning("Veuillez remplir l’énoncé, au moins deux réponses et cocher au moins une bonne réponse.")
    elif question_type == "QCU" and len(correct_answers) != 1:
        st.warning("Une QCU doit avoir une **seule** bonne réponse.")
    else:
        st.session_state.questions.append({
            "type": question_type,
            "statement": question_statement,
            "options": options,
            "correct": correct_answers
        })
        st.success("Question ajoutée.")
        st.session_state.question_counter += 1

st.divider()

# === 4. Liste et suppression de questions ===
st.header("📋 Questions créées")

if st.session_state.questions:
    for idx, q in enumerate(st.session_state.questions):
        st.markdown(f"**{idx+1}. [{q['type']}]** {q['statement']}")
        for opt in q["options"]:
            st.markdown(f"- {opt} {'✅' if opt in q['correct'] else ''}")
        if st.button(f"🗑 Supprimer la question {idx+1}", key=f"del_{idx}"):
            st.session_state.questions.pop(idx)
            st.experimental_rerun()
else:
    st.info("Aucune question ajoutée pour l’instant.")

# === 5. Score de validation ===
if st.session_state.questions:
    st.divider()
    st.subheader("🎯 Score de validation requis")

    total = len(st.session_state.questions)
    score = st.number_input(f"Score minimal pour réussir le quizz (sur {total})", min_value=1, max_value=total, value=max(1, total // 2))
    st.success(f"Score requis : {score}/{total}")

