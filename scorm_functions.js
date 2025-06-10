var API = null;

// 🔹 Détecter si le SCORM API est disponible (LMS)
function findAPI(win) {
    let tries = 0;
    while ((win.API == null) && (win.parent != null) && (win.parent != win)) {
        tries++;
        if (tries > 10) {
            console.warn("🚨 SCORM API introuvable après 10 tentatives.");
            return null;
        }
        win = win.parent;
    }
    return win.API;
}

// 🔹 Initialisation du SCORM
function initializeSCORM() {
    API = findAPI(window);
    if (API == null) {
        console.error("❌ SCORM API non trouvée. Le module pourrait ne pas enregistrer les données.");
        return;
    }

    let result = API.LMSInitialize("");
    if (result !== "true") {
        console.error("❌ Échec de l'initialisation SCORM !");
    } else {
        console.log("✅ SCORM Initialisé avec succès !");
    }

    let status = API.LMSGetValue("cmi.core.lesson_status");
    if (status === "not attempted" || status === "") {
        API.LMSSetValue("cmi.core.lesson_status", "incomplete");
        API.LMSCommit(""); // 📡 Enregistrement immédiat
    }
}

// 🔹 Enregistrement et validation SCORM (sans LMSFinish)
function setSCORMCompletion() {
    if (API == null) {
        console.error("❌ Impossible de mettre à jour le SCORM : API introuvable.");
        return;
    }

    console.log("✅ SCORM: Marquer comme complété");
    API.LMSSetValue("cmi.core.lesson_status", "completed");
    API.LMSSetValue("cmi.core.score.raw", "100");
    API.LMSCommit(""); // 📡 Enregistrement
}

// 🔹 Sauvegarde avant fermeture (sans LMSFinish)
window.onbeforeunload = function () {
    if (API != null) {
        console.log("⚠️ SCORM: Enregistrement avant fermeture");
        API.LMSCommit("");
    }
};
window.onunload = function () {
    if (API != null) {
        console.log("⚠️ SCORM: Fermeture détectée, enregistrement final");
        API.LMSCommit("");
    }
};
