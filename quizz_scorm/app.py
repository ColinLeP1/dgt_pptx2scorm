import streamlit as st

# Initialisation session
if "questions" not in st.session_state:
    st.session_state.questions = []
if "question_counter" not in st.session_state:
    st.session_state.question_counter = 0
if "option_counts" not in st.session_state:
    st.session_state.option_counts = {}

st.set_page_config(page_title="Créateur de Quizz", layout="centered")
st.title("📝 Créateur de Quizz")

# Infos générales
quiz_title = st.text_input("Titre du quizz")
quiz_description = st.text_area("Description du quizz")
uploaded_image = st.file_uploader("Importer une image", type=["png", "jpg", "jpeg"])
if uploaded_image:
    st.image(uploaded_image, use_column_width=True)

st.divider()

# Création question
st.header("Créer une nouvelle question")

question_type = st.selectbox("Type de question", ["Vrai / Faux", "QCU", "QCM"])
question_statement = st.text_area("Énoncé de la question")

q_id = st.session_state.question_counter
if q_id not in st.session_state.option_counts:
    if question_type == "Vrai / Faux":
        st.session_state.option_counts[q_id] = 2
    elif question_type == "QCU":
        st.session_state.option_counts[q_id] = 2
    else:
        st.session_state.option_counts[q_id] = 3

def add_option():
    st.session_state.option_counts[q_id] += 1

# Bouton uniquement pour **ajouter** des réponses
if st.button("➕ Ajouter une réponse", key="add_opt"):
    add_option()

num_options = st.session_state.option_counts[q_id]

options = []
correct_answers = []

st.markdown("**Choix et bonnes réponses :**")
for i in range(num_options):
    col1, col2 = st.columns([4, 1])
    with col1:
        opt = st.text_input(f"Réponse {i+1}", key=f"opt_{q_id}_{i}")
    with col2:
        is_correct = st.checkbox("✔", key=f"chk_{q_id}_{i}")
    if opt:
        options.append(opt)
        if is_correct:
            correct_answers.append(opt)

# Ajouter la question
if st.button("✅ Ajouter cette question"):
    min_opts = 2 if question_type == "QCU" else 3 if question_type == "QCM" else 2
    if not question_statement or len(options) < min_opts or not correct_answers:
        st.warning(f"Remplissez l’énoncé, au moins {min_opts} réponses et cochez au moins une bonne réponse.")
    elif question_type == "QCU" and len(correct_answers) != 1:
        st.warning("Pour une QCU, cochez une seule bonne réponse.")
    else:
        st.session_state.questions.append({
            "type": question_type,
            "statement": question_statement,
            "options": options,
            "correct": correct_answers
        })
        st.success("Question ajoutée.")
        st.session_state.question_counter += 1
        # Réinitialiser nombre options pour la prochaine question
        st.session_state.option_counts[q_id] = 2 if question_type=="QCU" else 3 if question_type=="QCM" else 2
        st.experimental_rerun()

st.divider()

# Liste des questions créées + suppression de question entière
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

# Score validation
if st.session_state.questions:
    st.divider()
    st.subheader("🎯 Score de validation requis")
    total = len(st.session_state.questions)
    score = st.number_input(f"Score minimal pour réussir le quizz (sur {total})", min_value=1, max_value=total, value=max(1, total // 2))
    st.success(f"Score requis : {score}/{total}")
