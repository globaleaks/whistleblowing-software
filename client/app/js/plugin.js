/* eslint no-unused-vars: ["error", { "varsIgnorePattern": "startGlobaLeaks" }] */

(function () {
   'use strict';

  function closeGlobaLeaks() {
    function deleteElementById(id) {
      var element = document.getElementById(id);
      element.parentNode.removeChild(element);
    }

    deleteElementById('globaleaks-overlay');
    deleteElementById('globaleaks-container');
  }

  function startGlobaLeaks(url) {
    var linkText = document.createTextNode('\u274C');

    var a = document.createElement('a');
    a.style.color = '#FFF';
    a.style['text-decoration'] = 'none';
    a.style['font-size'] = '20px';
    a.onclick = closeGlobaLeaks();
    a.appendChild(linkText);

    var ifrm = document.createElement('IFRAME');
    ifrm.overflow = 'hidden';
    ifrm.setAttribute('id', 'globaleaks-iframe');
    ifrm.setAttribute('src', url);
    ifrm.style.position = 'relative';
    ifrm.style.width = '100%';
    ifrm.style.height = '95%';
    ifrm.style.margin = 0;
    ifrm.style.border = 0;
    ifrm.style.top = 0;
    ifrm.style.left = 0;
    ifrm.style.right = 0;
    ifrm.style.bottom = 0;
    ifrm.style['z-index'] = 2147483647;
    ifrm.style['background-color'] = '#DDD';
    ifrm.style.border = '1px solid #000';
    ifrm.style.opacity = 1;

    var container = document.createElement('DIV');
    container.setAttribute('id', 'globaleaks-container');
    container.style.position = 'absolute';
    container.style.width = '95%';
    container.style.height = '95%';
    container.style.margin = '0px auto';
    container.style.border = 0;
    container.style.top = 0;
    container.style.left = 0;
    container.style.right = 0;
    container.style.bottom = 0;
    container.style['z-index'] = 2147483647;
    container.style['background-color'] = 'transparent';
    container.style['text-align'] = 'right';
    container.style.padding = '10px';
    container.style.border = 0;
    container.style.opacity = 1;

    var overlay = document.createElement('DIV');
    overlay.setAttribute('id', 'globaleaks-overlay');
    overlay.style.position = 'absolute';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.display = 'flex';
    overlay.style['align-items'] = 'center';
    overlay.style.top = 0;
    overlay.style.left = 0;
    overlay.style.right = 0;
    overlay.style['z-index'] = '2147483646';
    overlay.style['text-align'] = 'center';
    overlay.style['background-color'] = '#000';
    overlay.style['text-align'] = 'center';
    overlay.style.opacity = 0.7;

    container.appendChild(a);
    container.appendChild(ifrm);
    document.body.appendChild(container);
    document.body.appendChild(overlay);
    return ifrm;
  }
}());
