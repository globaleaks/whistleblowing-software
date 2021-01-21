GL.controller("LoginCtrl", ["$scope", "$location", "$filter",
function($scope, $location, $filter) {
  $scope.loginData = {
    loginUsername: "",
    loginPassword: "",
    loginAuthCode: ""
  };

  // If already logged in, just go to the landing page.
  if (typeof $scope.Authentication.session !== "undefined" && $scope.Authentication.session.homepage) {
    $location.path($scope.Authentication.session.homepage);
  }

  if ($location.path() === "/receipt") {
    $scope.login_template = "views/login/receipt.html";
  } else if ($location.path() === "/login" && $scope.public.node.simplified_login) {
    $scope.login_template = "views/login/simplified.html";
  } else if ($location.path() === "/multisitelogin" && $scope.public.node.multisite_login) {
    $scope.login_template = "views/login/multisite.html";

    if ($scope.public.node.mode === "whistleblowing.it") {
      $scope.loginData.loginUsername = "recipient";
    }
  } else {
    $scope.login_template = "views/login/default.html";
  }

  var token = $location.search().token;
  if (token) {
    $scope.Authentication.login(0, "", "", "", token);
    return;
  }

  if ($scope.public.node.root_tenant) {
    $scope.vars = {
      "site": null
    };

    $scope.selectSite = function(item) {
      $scope.vars.site = item;
    };

    $scope.refreshSelectableSites = function(search) {
      $scope.selectableSites = [];

      if (!$scope.public.sites) {
        return;
      };

      search = search.toLowerCase();

      $scope.selectableSites = $scope.public.sites.filter(function(item) {
        var text = item.name + item.subdomain;
        return text.toLowerCase().indexOf(search) !== -1 && item.id !== 1;
      });

      $scope.selectableSites = $filter("orderBy")($scope.selectableSites, "name");
    };
  }
}]);
