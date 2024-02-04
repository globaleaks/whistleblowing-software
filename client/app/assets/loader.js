function createAndAppendLink(href) {
  const link = document.createElement("link");
  link.setAttribute("rel", "stylesheet");
  link.setAttribute("type", "text/css");
  link.setAttribute("href", href);
  document.getElementsByTagName("head")[0].appendChild(link);
}

function createAndAppendScript(src) {
  const script = document.createElement("script");
  script.setAttribute("type", "text/javascript");
  script.setAttribute("src", src);
  document.getElementsByTagName("body")[0].appendChild(script);
}


createAndAppendLink("css/styles.css");
const scriptFiles = ["js/polyfills.js", "js/runtime.js", "js/main.js"];
for (const scriptFile of scriptFiles) {
  createAndAppendScript(scriptFile);
}
