GLClient.controller('AdminNetworkCtrl', ['$scope', function($scope) {
  $scope.active = 1;

  $scope.tabs = [
    {
      title:"Main configuration",
      template: "views/admin/network/main.html"
    },
    {
      title:"HTTPS settings",
      template: "views/admin/network/https_settings.html"
    },
  ];

  $scope.setActiveTab = function(index) {
    $scope.active = index;
  }
}]).
controller('AdminNetFormCtrl', [function() {
    // Scoped for future use.
}]).
controller('AdminHTTPSConfigCtrl', ['$http', '$scope', '$timeout', '$uibModal', 'FileSaver', 'AdminTLSConfigResource', 'AdminTLSCfgFileResource', 'Utils',
  function($http, $scope, $timeout, $uibModal, FileSaver, tlsConfigResource, cfgFileResource, Utils) {

  $scope.state = 0;

  $scope.parseTLSConfig = function(tlsConfig) {
    $scope.tls_config = tlsConfig;

    if (!$scope.admin.node.public_site || !tlsConfig.files.priv_key.set) {
      $scope.state = 0;
    } else if (tlsConfig.files.priv_key.gen && !tlsConfig.files.csr.set) {
      $scope.state = 1;
    } else if (!tlsConfig.files.cert.set) {
      $scope.state = 2
    } else if (!tlsConfig.files.chain.set) {
      $scope.state = 3;
    } else {
      $scope.state = 4;
    }
  }

  tlsConfigResource.get({}, $scope.parseTLSConfig);

  $scope.show_expert_status = false;
  $scope.invertExpertStatus = function() {
    $scope.show_expert_status = !$scope.show_expert_status;
  }

  function refreshPromise() {
    return tlsConfigResource.get({}, $scope.parseTLSConfig);
  }

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
    return $scope.file_resources.priv_key.$update().then(refreshPromise);
  }

  $scope.postFile = function(file, resource) {
    Utils.readFileAsText(file).then(function(str) {
      resource.content = str;
      return resource.$save();
    }).then(refreshPromise);
  };

  $scope.downloadFile = function(resource) {
     $http({
        method: 'GET',
        url: 'admin/config/tls/files/' + resource.name, // NOTE path
        responseType: 'blob',
     }).then(function (response) {
        FileSaver.saveAs(response.data, resource.name + '.pem');
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
      return resource.$delete().then(refreshPromise);
    };
    $uibModal.open({
      templateUrl: 'views/partials/admin_review_action.html',
      controller: 'AdminReviewModalCtrl',
      resolve: {
        targetFunc: function() { return targetFunc; },
      },
    });
  };

  // A helper function to give us a bit more resolution on the status of the
  // tls_config...
  function scheduleWithTimeouts(p, f, num, delay) {
    for (var i = 0; i < num; i++) {
        p = p.then(f).then($timeout(function(){}, delay));
    }
    return p;
  }

  $scope.toggleCfg = function() {
    var p;
    // TODO these posts send the entire tls_config object.
    // better for them to be removed.
    if ($scope.tls_config.enabled) {
      p = $scope.tls_config.$disable();

    } else {
      p = $scope.tls_config.$enable();
    }
    scheduleWithTimeouts(p, refreshPromise, 3, 2000);
  };

  $scope.deleteAll = function() {
    $scope.tls_config.$delete().then(refreshPromise);
  };

  $scope.submitCSR = function() {
    $scope.file_resources.content = $scope.csr_cfg;
    $scope.file_resources['csr'].content = $scope.csr_cfg;
    $scope.file_resources['csr'].$save().then(function() {
      $scope.csr_state.open = false;
      refreshPromise();
    });
  };
}]);
