GLClient.
controller("AdminNetworkCtrl", ["$scope", "$http", function($scope, $http) {
  $scope.tabs = [
    {
      title: "HTTPS",
      template: "views/admin/network/https.html"
    },
    {
      title: "Tor",
      template: "views/admin/network/tor.html"
    },
    {
      title: "Access control",
      template: "views/admin/network/access_control.html"
    },
    {
      title: "URL redirects",
      template: "views/admin/network/url_redirects.html"
    }
  ];

  $scope.hostname = $scope.resources.node.hostname;

  $scope.resetOnionPrivateKey = function() {
    var req = {
      "operation": "reset_onion_private_key",
      "args": {}
    };

    return $http({method: "PUT", url: "admin/config", data: req}).then(function(response) {
      $scope.resources.node.onionservice = response.data.onionservice;
    });
  };

  $scope.new_redirect = {};

  $scope.add_redirect = function() {
    var redirect = new $scope.AdminUtils.new_redirect();

    redirect.path1 = $scope.new_redirect.path1;
    redirect.path2 = $scope.new_redirect.path2;

    redirect.$save(function(new_redirect){
      $scope.resources.redirects.push(new_redirect);
      $scope.new_redirect = {};
    });
  };
}]).
controller("AdminHTTPSConfigCtrl", ["$q", "$location", "$http", "$scope", "$uibModal", "FileSaver", "AdminTLSConfigResource", "AdminTLSCfgFileResource", "AdminAcmeResource",
  function($q, $location, $http, $scope, $uibModal, FileSaver, tlsConfigResource, cfgFileResource, adminAcmeResource) {
  $scope.state = 0;
  $scope.menuState = "setup";
  $scope.showHostnameSetter = false;
  $scope.choseManCfg = false;
  $scope.saveClicked = false;
  $scope.skipVerify = $scope.resources.node.hostname !== "";

  $scope.setMenu = function(state) {
    $scope.menuState = state;
  };

  $scope.parseTLSConfig = function(tlsConfig) {
    $scope.tls_config = tlsConfig;

    var t = 0;
    var choice = "setup";

    if (!tlsConfig.acme) {
      if (tlsConfig.files.priv_key.set) {
        t = 1;
      }

      if (tlsConfig.files.cert.set) {
        t = 2;
      }

      if (tlsConfig.files.chain.set) {
        t = 3;
      }
    } else if (tlsConfig.files.priv_key.set &&
               tlsConfig.files.cert.set &&
               tlsConfig.files.chain.set) {
      t = 3;
    }

    if (tlsConfig.enabled) {
      choice = "status";
      t = -1;
    } else if (t > 0) {
      choice = "files";
    }

    $scope.state = t;
    $scope.menuState = choice;
  };

  tlsConfigResource.get({}).$promise.then($scope.parseTLSConfig);

  function refreshConfig() {
    return tlsConfigResource.get().$promise.then($scope.parseTLSConfig);
  }

  $scope.refreshCfg = refreshConfig;

  $scope.file_resources = {
    priv_key: new cfgFileResource({name: "priv_key"}),
    cert:     new cfgFileResource({name: "cert"}),
    chain:    new cfgFileResource({name: "chain"}),
    csr:      new cfgFileResource({name: "csr"}),
  };

  $scope.csr_cfg = {
    country: "",
    province: "",
    city: "",
    company: "",
    department: "",
    email: ""
  };

  $scope.csr_state = {
    open: false,
  };

  $scope.gen_priv_key = function() {
    return $scope.file_resources.priv_key.$update().then(refreshConfig);
  };

  $scope.postFile = function(file, resource) {
    $scope.Utils.readFileAsText(file).then(function(str) {
      resource.content = str;
      return resource.$save();
    }).then(refreshConfig);
  };

  $scope.downloadFile = function(resource) {
     $http({
        method: "GET",
        url: "admin/config/tls/files/" + resource.name,
        responseType: "blob",
     }).then(function (response) {
        FileSaver.saveAs(response.data, resource.name + ".pem");
     });
  };

  $scope.initAcme = function() {
    var aRes = new adminAcmeResource();
    $scope.file_resources.priv_key.$update()
    .then(function() {
        return aRes.$save();
    })
    .then(function(resp) {
      $scope.le_terms_of_service = resp.terms_of_service;
      $scope.setMenu("acme");
    });
  };

  $scope.completeAcme = function() {
    var aRes = new adminAcmeResource({});
    aRes.$update().then(refreshConfig);
  };

  $scope.statusClass = function(fileSum) {
    if (angular.isDefined(fileSum) && fileSum.set) {
      return {"text-success": true};
    } else {
      return {};
    }
  };

  $scope.deleteFile = function(resource) {
    var targetFunc = function() {
      return resource.$delete().then(refreshConfig);
    };

    $uibModal.open({
      templateUrl: "views/partials/admin_review_action.html",
      controller: "reviewModalCtrl",
      resolve: {
        targetFunc: function() { return targetFunc; },
      },
    });
  };

  $scope.chooseManCfg = function() {
    $scope.choseManCfg = true;
    $scope.setMenu("files");
  };

  $scope.toggleCfg = function() {
    // A promise which resolves only after a modal has been displayed
    var modal_open = $q.defer();

    if ($scope.tls_config.enabled) {
      if ($location.protocol() === "https") {
        // The next request is about to disable https meaning the interface is
        // about to be unreachable.
        $uibModal.open({
          templateUrl: "views/partials/disable_input.html",
          controller: "disableInputModalCtrl",
          resolve: {
            modal_open: function() { return modal_open; },
          },
        });

        modal_open.promise.then($scope.tls_config.$disable);
      } else {
        // Just disable https and refresh the interface
        modal_open.promise.then($scope.tls_config.$disable).then(refreshConfig);
        modal_open.resolve();
      }
    } {
      $scope.tls_config.$enable().then(refreshConfig);
    }
  };

  $scope.submitCSR = function() {
    $scope.file_resources.content = $scope.csr_cfg;
    $scope.file_resources["csr"].content = $scope.csr_cfg;
    $scope.file_resources["csr"].$save().then(function() {
      $scope.csr_state.open = false;
      return refreshConfig();
    });
  };

  $scope.toggleShowHostname = function() {
    $scope.showHostnameSetter = !$scope.showHostnameSetter;
  };

  $scope.resetCfg = function() {
    var targetFunc = function() {
      return $scope.tls_config.$delete().then(refreshConfig);
    };

    $uibModal.open({
      templateUrl: "views/partials/admin_review_action.html",
      controller: "reviewModalCtrl",
      resolve: {
        targetFunc: function() { return targetFunc; },
      },
    });
  };
}]).
controller("AdminRedirectEditCtrl", ["$scope", "AdminRedirectResource",
  function($scope, AdminRedirectResource) {
    $scope.delete_redirect = function(redirect) {
      AdminRedirectResource.delete({
        id: redirect.id
      }, function(){
        $scope.Utils.deleteFromList($scope.resources.redirects, redirect);
      });
    };
}]);
