GLClient.controller("LoginCtrl", ["$scope", "$location", "$filter", "Sites",
function($scope, $location, $filter, Sites) {
  $scope.loginData = {
    loginUsername: "",
    loginPassword: "",
    loginAuthCode: ""
  };

  // If already logged in, just go to the landing page.
  if ($scope.session !== undefined && $scope.session.auth_landing_page) {
    $location.path($scope.session.auth_landing_page);
  }

  if ($location.path() === "receipt") {
    $scope.login_template = "views/login/receipt.html";
  } else if ($location.path() === "/login" && $scope.node.simplified_login) {
    $scope.login_template = "views/login/simplified.html";
  } else if ($location.path() === "/multisitelogin" && $scope.node.multisite_login) {
    $scope.login_template = "views/login/multisite.html";

    if ($scope.node.mode === "whistleblowing.it") {
      $scope.loginUsername = "recipient";
    }
  } else {
    $scope.login_template = "views/login/default.html";
  }

  var token = $location.search().token;
  if (token) {
    $scope.Authentication.login(0, "", "", "", token);
    return;
  }

  if ($scope.node.root_tenant) {
    Sites.query(function(result) {
      $scope.vars = {
        "site": null
      };

      $scope.sites = result;
    });

    $scope.selectSite = function(item) {
      $scope.vars.site = item;
    };


    $scope.refreshSelectableSites = function(search) {
      if (!$scope.sites) {
        $scope.selectableSites = [];
        return;
      }

      search = search.toLowerCase();

      var ret = $scope.sites;
      ret = ret.filter(function(item) {
        return item.label.toLowerCase().indexOf(search) !== -1 && item.id !== 1;
      });

      $scope.selectableSites = $filter("orderBy")(ret, "label");
    };

    $scope.refreshSelectableSites();
  }
}]);
