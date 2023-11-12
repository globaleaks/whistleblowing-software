/* eslint-disable no-undef */

var mediaViewer = document.getElementById("media-viewer");
var pdfViewer = document.getElementById("pdf-viewer");
var pdfCanvas = document.getElementById("pdf-canvas");
var pdfControlNext = document.getElementById("next-page-btn");
var pdfControlPrev = document.getElementById("prev-page-btn");
var pdfControlPage = document.getElementById("page-number");
var pdfControlPageCount = document.getElementById("page-count");
var pdfDoc = null;
var pageNum = 1;
var pageCount = 0;

function receiveMessage(evt) {
  var url = URL.createObjectURL(evt.data.blob);
  if (evt.data.tag === "pdf") {
    pdfViewer.style.display = "block";
    mediaViewer.style.display = "none";
    createPdfViewer(url);
  } else {
    pdfViewer.style.display = "none";
    mediaViewer.style.display = "block";
    if (evt.data.tag === "audio") {
      mediaViewer.innerHTML =
        "<audio id=\"viewer\" src=\"" + url + "\" controls /></audio>";
    } else if (evt.data.tag === "image") {
      mediaViewer.innerHTML =
        "<img id=\"viewer\" src=\"" + url + "\" />";
    } else if (evt.data.tag === "video") {
      mediaViewer.innerHTML =
        "<video id=\"viewer\" src=\"" + url + "\" controls /></video>";
    } else if (evt.data.tag === "txt"){
      evt.data.blob.text().then(function(text) {
        mediaViewer.innerHTML =
          "<pre id=\"viewer\">" + text + "</pre>";
      });
    }
  }
}

function createPdfViewer(url) {
  pdfjsLib.getDocument(url).promise.then(function (pdfDoc_) {
    pdfDoc = pdfDoc_;
    pageCount = pdfDoc.numPages;
    pdfControlPageCount.innerHTML = pageCount;
    pdfControlPage.innerText = 0;
    renderPage(pageNum);
  });

  pdfControlNext.addEventListener("click", pdfNextPage);
  pdfControlPrev.addEventListener("click", pdfPrevPage);
}

function renderPage(num) {
  pdfDoc.getPage(num).then(function (page) {
    // find scale to fit page in canvas
    var scale = pdfCanvas.clientWidth / page.getViewport({ scale: 1.0 }).width;
    var viewport = page.getViewport({ scale: scale});
    var canvas = pdfCanvas;
    var context = canvas.getContext("2d");
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    var renderContext = {
      canvasContext: context,
      viewport: viewport,
    };
    var renderTask = page.render(renderContext);
    renderTask.promise.then(function () {
      // updating label
      pdfControlPage.innerText = pageNum;
      // disable and enable control buttons
      if (pageNum <= 1) {
        pdfControlPrev.disabled = true;
      }
      if (pageNum >= pageCount) {
        pdfControlNext.disabled = true;
      }
      if (pageNum > 1) {
        pdfControlPrev.disabled = false;
      }
      if (pageNum < pageCount) {
        pdfControlNext.disabled = false;
      }
    });
  });
}

function pdfNextPage() {
  if (pageNum >= pageCount) {
    return;
  }
  pageNum++;
  pdfControlPage.value = pageNum;
  renderPage(pageNum);
}

function pdfPrevPage() {
  if (pageNum <= 1) {
    return;
  }
  pageNum--;
  pdfControlPage.value = pageNum;
  renderPage(pageNum);
}

window.addEventListener(
  "load",
  function () {
    if (window.self === window.top) {
      return;
    };

    window.parent.postMessage("ready", "*");
    window.addEventListener("message", receiveMessage, { once: true });
  },
  true
);

window.addEventListener(
  "unload",
  function () {
    pdfControlNext.removeEventListener("click", pdfNextPage);
    pdfControlPrev.removeEventListener("click", pdfPrevPage);
  },
  true
);
