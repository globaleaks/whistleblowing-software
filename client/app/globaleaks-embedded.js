function closeGlobaLeaks() {
  function deleteElementById(id) {
    var element = document.getElementById(id);
    element.parentNode.removeChild(element);
  }

  deleteElementById("globaleaks-app-overlay");
  deleteElementById("globaleaks-app");
}

function startGlobaLeaks(url) {
  var linkText = document.createTextNode("\u274C");

  var a = document.createElement("a");
  a.setAttribute("id", "globaleaks-app-close-button");
  a.onclick = closeGlobaLeaks;
  a.appendChild(linkText);

  var ifrm = document.createElement("IFRAME");
  ifrm.setAttribute("id", "globaleaks-app-iframe");
  ifrm.setAttribute("src", url);

  var app = document.createElement("DIV");
  app.setAttribute("id", "globaleaks-app");

  var overlay = document.createElement("DIV");
  overlay.setAttribute("id", "globaleaks-app-overlay");

  app.appendChild(a);
  app.appendChild(ifrm);

  document.body.appendChild(overlay);
  document.body.appendChild(app);

  return ifrm;
}
