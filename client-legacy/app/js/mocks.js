GL.mockEngine = (function() {
  var mocks = {};

  var applyMock = function (mock) {
    var e = document.querySelector(mock.selector);
    if (e) {
      if (!mock.value || mock.language !== GL.language) {
        mock.language = GL.language;
        if (typeof mock.mock === "function") {
          mock.value = mock.mock(e);
        } else {
          mock.value = mock.mock;
        }
      }

      if (mock.type === "replace") {
        if (mock.value && e.innerHTML !== mock.value) {
          e.innerHTML = mock.value;
        }

        if (mock.value) {
          mock.value = e.innerHTML;
        }
      } else {
        var custom_elem = e.querySelector(".Mock");

        if (!custom_elem) {
          custom_elem = document.createElement("div");
          custom_elem.classList.add("Mock");
        }

        custom_elem.innerHTML = mock.value;

        if (mock.type === "add-before") {
          e.insertBefore(custom_elem, e.childNodes[0]);
        } else if (mock.type === "add-after") {
          e.appendChild(custom_elem);
        }
      }
    }
  };

  var run = function() {
    var current_path = document.location.pathname + document.location.hash.split("?")[0];
    var path, selector, i;

    for (path in mocks) {
      if (path === "*" || path === current_path) {
	for (selector in mocks[path]) {
          for (i in mocks[path][selector]) {
            try {
              applyMock(mocks[path][selector][i]);
            } catch(e) {
              continue;
            }
          }
        }
      }
    }
  };

  var addMock = function(path, selector, mock, type) {
    if(!(path in mocks)) {
      mocks[path] = {};
    }

    if(!(selector in mocks[path])) {
      mocks[path][selector] = [];
    }

    if (type === undefined) {
      type = "replace";
    }

    mocks[path][selector].push({"path": path, "selector": selector, "mock": mock, "value": "", "type": type});

    run();
  };

  return {
    addMock: addMock,
    run: run
  };
}());
