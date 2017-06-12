GLClient.controller('AdminNetworkCtrl', ['$scope', function($scope) {
  $scope.active = 1; //TODO change to 0

  $scope.tabs = [
    {
      title:"Main configuration",
      template: "views/admin/network/main.html"
    },
    {
      title:"HTTPS settings",
      template: "views/admin/network/https_menu.html"
    },
    {
      title:"Access control",
      template: "views/admin/network/access_control.html"
    }
  ];

  $scope.setActiveTab = function(index) {
    $scope.active = index;
  }
}]).
controller('AdminNetFormCtrl', ['$scope', function($scope) {

}]).
controller('AdminHTTPSConfigCtrl', ['$q', '$http', '$scope', '$uibModal', 'FileSaver', 'AdminTLSConfigResource', 'AdminTLSCfgFileResource', 'AdminAcmeResource', 'Utils',
  function($q, $http, $scope, $uibModal, FileSaver, tlsConfigResource, cfgFileResource, adminAcmeResource, Utils) {

  $scope.state = 0;
  $scope.menuState = 'setup';
  $scope.showHostnameSetter = false;

  $scope.setMenu = function(state) {
    $scope.menuState = state;
  };

  $scope.verifyFailed = false;
  $scope.updateHostname = function() {
    return $scope.admin.node.$update().$promise.then(function() {
      $scope.showHostnameSetter = false;
      return $http({
        method: 'POST',
        url: '/admin/config/tls/hostname',
      })
    }).then(function() {
      $scope.verifyFailed = false;
    }, function() {
      $scope.verifyFailed = true;
    });
  }

  $scope.parseTLSConfig = function(tlsConfig) {
    $scope.tls_config = tlsConfig;

    var t = 0;
    if (tlsConfig.files.priv_key.set) {
      t = 1;
    }
    if (tlsConfig.files.cert.set) {
      t = 2
    }
    if (tlsConfig.files.chain.set) {
      t = 3;
    }
    if (tlsConfg.enabled) {
      t = -1;
    }
    $scope.state = t

    // Determine which window we need to show
    var choice = 'setup';
    if (tlsConfig.enabled) {
      choice = 'status';
    } else if ($scope.state > 0) {
      choice = 'fileRes';
    }
    $scope.menuState = choice;
  };

  tlsConfigResource.get({}, $scope.parseTLSConfig);

  $scope.show_expert_status = false;
  $scope.invertExpertStatus = function() {
    $scope.show_expert_status = !$scope.show_expert_status;
    return refreshConfig();
  };

  function refreshConfig() {
    return tlsConfigResource.get({}, $scope.parseTLSConfig).$promise;
  };

  $scope.refreshCfg = refreshConfig;

  $scope.file_resources = {
    priv_key: new cfgFileResource({name: 'priv_key'}),
    cert:     new cfgFileResource({name: 'cert'}),
    chain:    new cfgFileResource({name: 'chain'}),
    csr:      new cfgFileResource({name: 'csr'}),
  };

  $scope.csr_cfg = {
    country: '',
    province: '',
    city: '',
    company: '',
    department: '',
    email: '',
    commonname: '',
  };

  $scope.csr_state = {
    open: false,
  };

  $scope.gen_priv_key = function() {
    return $scope.file_resources.priv_key.$update().then(refreshConfig);
  };

  $scope.postFile = function(file, resource) {
    Utils.readFileAsText(file).then(function(str) {
      resource.content = str;
      return resource.$save();
    }).then(refreshConfig);
  };

  $scope.downloadFile = function(resource) {
     $http({
        method: 'GET',
        url: 'admin/config/tls/files/' + resource.name,
        responseType: 'blob',
     }).then(function (response) {
        FileSaver.saveAs(response.data, resource.name + '.pem');
     });
  };

  $scope.runInitAutoAcme = function() {
    var aRes = new adminAcmeResource();
    $scope.file_resources.priv_key.$update()
    .then(function() {
        return aRes.$save();
    })
    .then(function(resp) {
      $scope.le_terms_of_service = resp.terms_of_service;
      $scope.setMenu('acmeCfg');
    });
  };

  $scope.letsEncryptor = function() {
    var aRes = new adminAcmeResource({});
    aRes.$update().then(function() {
      $scope.csr_state.open = false;
      $scope.setMenu('acmeFin');
    });
  };

  $scope.statusClass = function(fileSum) {
    if (angular.isDefined(fileSum) && fileSum.set) {
        return {'text-success': true};
    } else {
        return {};
    }
  };

  $scope.deleteFile = function(resource) {
    var targetFunc = function() {
      return resource.$delete().then(refreshConfig);
    };
    $uibModal.open({
      templateUrl: 'views/partials/admin_review_action.html',
      controller: 'AdminReviewModalCtrl',
      resolve: {
        targetFunc: function() { return targetFunc; },
      },
    });
  };

  $scope.choseManCfg = false;
  $scope.chooseManCfg = function() {
    $scope.choseManCfg = true;
    $scope.setMenu('fileRes');
  }
$scope.toggleCfg = function() {
    // TODO these posts send the entire tls_config object. They should be removed.
    if ($scope.tls_config.enabled) {
      var p = $scope.tls_config.$disable();
      return p.then(refreshConfig);
    } else {
      var go_url = 'https://' + $scope.admin.node.hostname + '/#/admin/network';
      var open_promise = $q.defer();

      $uibModal.open({
        backdrop: 'static',
        keyboad: false,
        templateUrl: '/views/admin/network/redirect_to_https.html',
        controller: 'safeRedirectModalCtrl',
        resolve: {
          https_url: function() { return go_url; },
          open_promise: function() { return open_promise; },
        },
      });

      open_promise.then($scope.tls_config.$enable);
    }
  };

  $scope.deleteAll = function() {
    $scope.tls_config.$delete().then(refreshConfig);
  };

  $scope.submitCSR = function() {
    $scope.file_resources.content = $scope.csr_cfg;
    $scope.file_resources['csr'].content = $scope.csr_cfg;
    $scope.file_resources['csr'].$save().then(function() {
      $scope.csr_state.open = false;
      return refreshConfig();
    });
  };

  $scope.toggleShowHostname = function() {
    $scope.showHostnameSetter = !$scope.showHostnameSetter;
  }

  $scope.deleteEverything = function() {
    $scope.tls_config.$delete().then(refreshConfig);
  }
}])
.controller('safeRedirectModalCtrl', ['$scope', '$timeout', '$http', function($scope, $timeout, $http) {
    // NOTE this resolves a creation promise for the containing ctrl
    $scope.$resolve.open_promise.resolve();

    $scope.state = '1';
    var p = $http({
        method: 'GET',
        url: 'https://' + $scope.admin.node.hostname + '/robots.txt',
    }).then(function() { // Succeeded
        $scope.state = '2';
        $timeout(function() {
          location.reload();
        }, 15000);
    }, function() { // Failed
        $scope.state = '3';
    });
}]);
