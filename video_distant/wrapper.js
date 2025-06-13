import scorm from "pipwerks-scorm-api-wrapper";

console.log("wrapper.js chargé");

// Fonction d'initialisation SCORM avec logs
function init() {
  console.log("Début init SCORM");
  const initResult = scorm.init();
  console.log("scorm.init() returned:", initResult);

  // Exemple : marquer le statut incomplet au départ
  scorm.set("cmi.core.lesson_status", "incomplete");
  scorm.save();
}

// Fonction globale pour marquer la complétion
window.setCompleted = function () {
  scorm.set("cmi.core.lesson_status", "completed");
  scorm.save();
  console.log("Module marqué comme complété.");
};

// Appel automatique de init au chargement
init();

// Appel scorm.quit() avant fermeture pour sauvegarder
window.addEventListener("beforeunload", function () {
  scorm.quit();
  console.log("scorm.quit() appelé avant fermeture");
});
