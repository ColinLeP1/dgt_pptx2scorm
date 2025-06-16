import streamlit as st

# Initialisation session
if "questions" not in st.session_state:
    st.session_state.questions = []
if "question_counter" not in st.session_state:
    st.session_state.question_counter = 0
if "questions_data" not in st.session_state:
    st.session_state.questions_data = {}
if "refresh" not in st.session_state:
    st.session_state.refresh = 0  # compteur pour forcer mise à jour

st.set_page_config(page_title="Créateur de Quizz", layout="centered")
st.title("📝 Créateur de Quizz")

# Quiz infos
quiz_title = st.text_input("Titre du quizz")
quiz_description = st.text_area("Description du quizz")
uploaded_image = st.file_uploader("Importer une image", type=["png", "jpg", "jpeg"])
if uploaded_image:
    st.image(uploaded_image, use_column_width=True)

st.divider()

# --- Création question ---
st.header("Créer une nouvelle question")

question_type = st.selectbox("Type de question", ["Vrai / Faux", "QCU", "QCM"])
question_statement = st.text_area("Énoncé de la question")

qid = st.session_state.question_counter

if qid not in st.session_state.questions_data:
    if question_type == "Vrai / Faux":
        st.session_state.questions_data[qid] = {
            "options": ["Vrai", "Faux"],
            "correct": [False, False]
        }
    elif question_type == "QCU":
        st.session_state.questions_data[qid] = {
            "options": ["", ""],
            "correct": [False, False]
        }
    else:
        st.session_state.questions_data[qid] = {
            "options": ["", "", ""],
            "correct": [False, False, False]
        }

data = st.session_state.questions_data[qid]

def update_option_text(index, new_text):
    data["options"][index] = new_text

def toggle_correct(index):
    if question_type == "QCU":
        data["correct"] = [False]*len(data["correct"])
        data["correct"][index] = True
    else:
        data["correct"][index] = not data["correct"][index]

def delete_option(index):
    min_opts = 2 if question_type == "QCU" else 3
    if question_type != "Vrai / Faux" and len(data["options"]) > min_opts:
        data["options"].pop(index)
        data["correct"].pop(index)

# Affichage options
st.markdown("**Options de réponse (cochez la ou les bonnes réponses) :**")

for i in range(len(data["options"])):
    cols = st.columns([6,1,1])
    with cols[0]:
        txt = st.text_input(f"Réponse {i+1}", value=data["options"][i], key=f"opt_{qid}_{i}")
        update_option_text(i, txt)
    with cols[1]:
        checked = st.checkbox("", value=data["correct"][i], key=f"chk_{qid}_{i}", on_change=toggle_correct, args=(i,))
    with cols[2]:
        can_delete = question_type != "Vrai / Faux" and len(data["options"]) > (2 if question_type == "QCU" else 3)
        if can_delete:
            if st.button("🗑", key=f"del_{qid}_{i}"):
                delete_option(i)
                st.session_state.refresh += 1  # on force une mise à jour

# Bouton ajouter une réponse (QCU/QCM uniquement)
if question_type != "Vrai / Faux":
    if st.button("➕ Ajouter une réponse"):
        data["options"].append("")
        data["correct"].append(False)
        st.session_state.refresh += 1  # force mise à jour

# Bouton ajouter la question
if st.button("✅ Ajouter cette question"):
    min_opts = 2 if question_type == "QCU" else 3 if question_type == "QCM" else 2
    opts_filled = all(opt.strip() != "" for opt in data["options"])
    if not question_statement.strip():
        st.warning("L'énoncé ne peut pas être vide.")
    elif len(data["options"]) < min_opts:
        st.warning(f"Il doit y avoir au moins {min_opts} réponses.")
    elif not opts_filled:
        st.warning("Toutes les réponses doivent être remplies.")
    elif not any(data["correct"]):
        st.warning("Au moins une bonne réponse doit être cochée.")
    elif question_type == "QCU" and data["correct"].count(True) != 1:
        st.warning("Pour le QCU, une seule bonne réponse doit être cochée.")
    else:
        st.session_state.questions.append({
            "type": question_type,
            "statement": question_statement,
            "options": data["options"],
            "correct": [data["options"][i] for i, c in enumerate(data["correct"]) if c]
        })
        st.success("Question ajoutée.")
        st.session_state.question_counter += 1
        st.session_state.questions_data.pop(qid)
        st.session_state.refresh += 1  # force update

st.divider()

# Affichage questions créées
st.header("📋 Questions créées")
if st.session_state.questions:
    for idx, q in enumerate(st.session_state.questions):
        st.markdown(f"**{idx+1}. [{q['type']}]** {q['statement']}")
        for opt in q["options"]:
            st.markdown(f"- {opt} {'✅' if opt in q['correct'] else ''}")
        if st.button(f"🗑 Supprimer la question {idx+1}", key=f"del_question_{idx}"):
            st.session_state.questions.pop(idx)
            st.session_state.refresh += 1  # force update
else:
    st.info("Aucune question ajoutée pour l’instant.")

# Score validation
if st.session_state.questions:
    st.divider()
    st.subheader("🎯 Score de validation requis")
    total = len(st.session_state.questions)
    score = st.number_input(f"Score minimal pour réussir le quizz (sur {total})", min_value=1, max_value=total, value=max(1, total//2))
    st.success(f"Score requis : {score}/{total}")

# Forcer le rafraîchissement quand refresh change
_ = st.session_state.refresh
