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
    return $scope.Utils.runAdminOperation("reset_onion_private_key", {}, true);
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
controller("AdminHTTPSConfigCtrl", ["$q", "$http", "$window", "$scope", "$uibModal", "AdminTLSConfigResource", "AdminTLSCfgFileResource", "AdminAcmeResource", "Utils",
  function($q, $http, $window, $scope, $uibModal, tlsConfigResource, cfgFileResource, adminAcmeResource, Utils) {
  $scope.state = 0;
  $scope.menuState = "setup";

  $scope.setup = function() {
    $scope.menuState = "files";
  };

  $scope.parseTLSConfig = function(tlsConfig) {
    $scope.tls_config = tlsConfig;

    var t = 0;

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
      t = -1;
      $scope.menuState = "status";
    } else if (t > 0) {
      $scope.menuState = "files";
    }

    $scope.state = t;
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

  $scope.deleteFile = function(resource) {
    $uibModal.open({
      templateUrl: "views/modals/confirmation.html",
      controller: "ConfirmableModalCtrl",
      resolve: {
        arg: null,
        confirmFun: function() { return function() { return resource.$delete().then($scope.refreshConfig); }; },
        cancelFun: null
      },
    });
  };

  $scope.setupAcme = function() {
    var aRes = new adminAcmeResource();
    $scope.file_resources.key.$update()
    .then(function() {
      return aRes.$save();
    }).then($scope.refreshConfig);
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

  $scope.generateCSR = function() {
    $http.post("api/admin/config/csr/gen", $scope.csr_cfg).then(function (response) {
       Utils.saveAs(new Blob([response.data], {type: "text/plain;charset=utf-8"}), "csr.pem");
    });
  };

  $scope.resetCfg = function() {
    $uibModal.open({
      templateUrl: "views/modals/confirmation.html",
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
