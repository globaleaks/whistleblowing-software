GL.
controller("AdminNetworkCtrl", ["$scope", function($scope) {
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

  $scope.resetOnionPrivateKey = function() {
    return $scope.Utils.applyConfig("reset_onion_private_key", {}, true);
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
controller("AdminHTTPSConfigCtrl", ["$q", "$http", "$window", "$scope", "$uibModal", "FileSaver", "AdminTLSConfigResource", "AdminTLSCfgFileResource", "AdminAcmeResource",
  function($q, $http, $window, $scope, $uibModal, FileSaver, tlsConfigResource, cfgFileResource, adminAcmeResource) {
  $scope.state = 0;
  $scope.menuState = "setup";

  $scope.setMenu = function(state) {
    $scope.menuState = state;
  };

  $scope.parseTLSConfig = function(tlsConfig) {
    $scope.tls_config = tlsConfig;

    var t = 0;
    var choice = "setup";

    if (!tlsConfig.acme) {
      if (tlsConfig.files.key.set) {
        t = 1;
      }

      if (tlsConfig.files.cert.set) {
        t = 2;
      }

      if (tlsConfig.files.chain.set) {
        t = 3;
      }
    } else if (tlsConfig.files.key.set &&
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

  $scope.refreshConfig = function() {
    return tlsConfigResource.get().$promise.then($scope.parseTLSConfig);
  };

  $scope.file_resources = {
    key: new cfgFileResource({name: "key"}),
    cert: new cfgFileResource({name: "cert"}),
    chain: new cfgFileResource({name: "chain"}),
    csr: new cfgFileResource({name: "csr"}),
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

  $scope.gen_key = function() {
    return $scope.file_resources.key.$update().then($scope.refreshConfig);
  };

  $scope.postFile = function(file, resource) {
    $scope.Utils.readFileAsText(file).then(function(str) {
      resource.content = str;
      return resource.$save();
    }).then($scope.refreshConfig);
  };

  $scope.downloadFile = function(resource) {
    $http({
       method: "GET",
       url: "api/admin/config/tls/files/" + resource.name,
       responseType: "blob",
    }).then(function (response) {
       FileSaver.saveAs(response.data, resource.name + ".pem");
    });
  };

  $scope.setupAcme = function() {
    var aRes = new adminAcmeResource();
    $scope.file_resources.key.$update()
    .then(function() {
      return aRes.$save();
    }).then($scope.refreshConfig);
  };

  $scope.deleteFile = function(resource) {
    $uibModal.open({
      templateUrl: "views/partials/admin_review_action.html",
      controller: "ConfirmableModalCtrl",
      resolve: {
        arg: null,
        confirmFun: function() { return function() { return resource.$delete().then($scope.refreshConfig); }; },
        cancelFun: null
      },
    });
  };

  $scope.setup = function() {
    $scope.setMenu("files");
  };

  $scope.toggleCfg = function() {
    if ($scope.tls_config.enabled) {
      $scope.tls_config.$disable().then($scope.refreshConfig);
    } else {
      $scope.tls_config.$enable().then(function() {
        $window.location.href = "https://" + $scope.resources.node.hostname;
      });
    }
  };

  $scope.submitCSR = function() {
    $scope.file_resources.content = $scope.csr_cfg;
    $scope.file_resources.csr.content = $scope.csr_cfg;
    $scope.file_resources.csr.$save().then(function() {
      $scope.csr_state.open = false;
      return $scope.refreshConfig();
    });
  };

  $scope.resetCfg = function() {
    $uibModal.open({
      templateUrl: "views/partials/admin_review_action.html",
      controller: "ConfirmableModalCtrl",
      resolve: {
	arg: null,
        confirmFun: function() { return function() { $scope.tls_config.$delete().then($scope.refreshConfig); }; },
        cancelFun: null
      }
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
