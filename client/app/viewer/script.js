function receiveMessage (evt) {
  var url = URL.createObjectURL(evt.data.blob);

  if (evt.data.tag === "audio" ) {
    document.body.innerHTML = "<audio id=\"viewer\" src=\"" + url + "\" controls /></audio>";
  } else if (evt.data.tag === "image" ) {
    document.body.innerHTML = "<img id=\"viewer\" src=\"" + url + "\" />";
  } else if (evt.data.tag === "video" ) {
    document.body.innerHTML = "<video id=\"viewer\" src=\"" + url + "\" controls /></video>";
  }
}

window.addEventListener("message", receiveMessage, {once: true});
window.parent.postMessage("ready", "*");
