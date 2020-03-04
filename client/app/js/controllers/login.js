GLClient.controller("LoginCtrl", ["$scope", "$location", "$filter", "Sites",
function($scope, $location, $filter, Sites) {
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
        var text = item.label+item.subdomain;
        return text.toLowerCase().indexOf(search) !== -1 && item.id !== 1;
      });

      $scope.selectableSites = $filter("orderBy")(ret, "label");
    };

    $scope.refreshSelectableSites();
  }
}]);
