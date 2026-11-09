// Escuta apenas respostas já carregadas pela página inspecionada.
// Sem fetch, cookies, tokens, credenciais ou upload.
chrome.devtools.panels.create("Salamito", "", "panel.html", () => {});
