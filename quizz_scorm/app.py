import streamlit as st

st.set_page_config(page_title="Créateur de Quizz", layout="wide")
st.title("📝 Créateur de Quizz dynamique")

# Initialisation
if "questions_data" not in st.session_state:
    st.session_state.questions_data = []

def create_empty_question():
    return {
        "type": "Vrai / Faux",
        "statement": "",
        "options": ["Vrai", "Faux"],
        "correct": [False, False]
    }

# Ajouter une nouvelle question vide
if st.button("➕ Ajouter une nouvelle question"):
    st.session_state.questions_data.append(create_empty_question())

# Fonction pour gérer les modifications des réponses
def update_option_text(q_idx, opt_idx, new_text):
    st.session_state.questions_data[q_idx]["options"][opt_idx] = new_text

def toggle_correct(q_idx, opt_idx):
    q = st.session_state.questions_data[q_idx]
    if q["type"] == "QCU":
        # une seule bonne réponse
        q["correct"] = [False] * len(q["correct"])
        q["correct"][opt_idx] = True
    else:
        q["correct"][opt_idx] = not q["correct"][opt_idx]

def delete_option(q_idx, opt_idx):
    q = st.session_state.questions_data[q_idx]
    min_opts = 2 if q["type"] == "QCU" else 3
    if q["type"] != "Vrai / Faux" and len(q["options"]) > min_opts:
        q["options"].pop(opt_idx)
        q["correct"].pop(opt_idx)

def change_question_type(q_idx, new_type):
    q = st.session_state.questions_data[q_idx]
    if new_type == "Vrai / Faux":
        q["type"] = new_type
        q["options"] = ["Vrai", "Faux"]
        q["correct"] = [False, False]
    elif new_type == "QCU":
        q["type"] = new_type
        # Minimum 2 options
        if len(q["options"]) < 2:
            q["options"] = q["options"][:2] + [""] * (2 - len(q["options"]))
            q["correct"] = [False]*2
    else:  # QCM
        q["type"] = new_type
        # Minimum 3 options
        if len(q["options"]) < 3:
            q["options"] = q["options"][:3] + [""] * (3 - len(q["options"]))
            q["correct"] = [False]*3

def add_option(q_idx):
    q = st.session_state.questions_data[q_idx]
    if q["type"] != "Vrai / Faux":
        q["options"].append("")
        q["correct"].append(False)

def delete_question(q_idx):
    st.session_state.questions_data.pop(q_idx)

# Affichage des questions avec expanders
for q_idx, question in enumerate(st.session_state.questions_data):
    with st.expander(f"Question {q_idx+1} : {question['statement'][:40] + ('...' if len(question['statement']) > 40 else '')}", expanded=True):
        cols = st.columns([3,1])
        with cols[0]:
            new_type = st.selectbox(f"Type de question #{q_idx+1}", ["Vrai / Faux", "QCU", "QCM"], index=["Vrai / Faux", "QCU", "QCM"].index(question["type"]), key=f"type_{q_idx}")
            if new_type != question["type"]:
                change_question_type(q_idx, new_type)
            new_statement = st.text_area(f"Énoncé question #{q_idx+1}", value=question["statement"], key=f"statement_{q_idx}")
            st.session_state.questions_data[q_idx]["statement"] = new_statement
        with cols[1]:
            if st.button("🗑 Supprimer la question", key=f"del_q_{q_idx}"):
                delete_question(q_idx)
                st.experimental_rerun()  # ici, c'est possible car on est en version récente ?

        st.markdown("**Réponses :**")
        for opt_idx, option in enumerate(question["options"]):
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1:
                new_opt_text = st.text_input(f"Réponse {opt_idx+1} de la question {q_idx+1}", value=option, key=f"opt_{q_idx}_{opt_idx}")
                update_option_text(q_idx, opt_idx, new_opt_text)
            with col2:
                checked = st.checkbox("", value=question["correct"][opt_idx], key=f"chk_{q_idx}_{opt_idx}", on_change=toggle_correct, args=(q_idx,opt_idx))
            with col3:
                can_delete = question["type"] != "Vrai / Faux" and len(question["options"]) > (2 if question["type"] == "QCU" else 3)
                if can_delete:
                    if st.button("🗑", key=f"del_opt_{q_idx}_{opt_idx}"):
                        delete_option(q_idx, opt_idx)
                        st.experimental_rerun()

        if question["type"] != "Vrai / Faux":
            if st.button(f"➕ Ajouter une réponse à la question {q_idx+1}", key=f"add_opt_{q_idx}"):
                add_option(q_idx)
                st.experimental_rerun()

st.divider()

# Score validation
total = len(st.session_state.questions_data)
if total > 0:
    st.subheader("🎯 Score de validation requis")
    score = st.number_input(f"Score minimal pour réussir le quizz (sur {total})", min_value=1, max_value=total, value=max(1, total//2))
    st.success(f"Score requis : {score} / {total}")

