GLClient.mockEngine = (function() {
  var mocks = {};

  var applyMock = function (selector, mock) {
    var e = document.querySelector(selector);
    if (e) {
      if (typeof mock === "function") {
        mock = mock(e);
      }

      if (mock && e.innerHTML !== mock) {
        e.innerHTML = mock;
      }
    }
  };

  var run = function() {
    var current_path = document.location.pathname + document.location.hash;
    var path, i;

    for (path in mocks) {
      if (path === "*" || path === current_path) {
        for (i=0; i<mocks[path].length; i++) {
          applyMock(mocks[path][i][0], mocks[path][i][1]);
        }
      }
    }
  };

  var addMock = function(path, selector, mock) {
    if(!(path in mocks)) {
      mocks[path] = [];
    }

    mocks[path].push([selector, mock]);

    run(null);
  };

  return {
    addMock: addMock,
    run: run
  };
}());
