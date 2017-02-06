GLClient.controller('AdminNetworkCtrl', ['$scope', function($scope) {
  $scope.tabs = [
    {
      title:"Main configuration",
      template: "views/admin/network/settings.html"
    },
    {
      title:"HTTPS dashboard",
      template: "views/admin/network/https_dash.html"
    },
  ];
}]).
controller('AdminNetFormCtrl', [function() {
    // Scoped for future use.
}]).
controller('AdminHTTPSConfigCtrl', ['$window', '$q', '$http', '$scope', '$uibModal', 'FileReader', 'FileSaver', 'AdminTLSConfigResource', 'AdminCSRConfigResource', 'AdminTLSCfgFileResource',
  function($window, $q, $http, $scope, $uibModal, FileReader, FileSaver, tlsConfigResource, csrCfgResource, cfgFileResource) {
  $scope.tls_config = tlsConfigResource.get();

  function refreshPromise() {
    return $scope.tls_config.$get().$promise;
  }

  $scope.file_resources = {
    priv_key: new cfgFileResource({name: 'priv_key'}),
    cert:     new cfgFileResource({name: 'cert'}),
    chain:    new cfgFileResource({name: 'chain'}),
  };

  $scope.csr_cfg = new csrCfgResource({
    country: '',
    province: '',
    city: '',
    company: '',
    department: '',
    email: '',
    commonname: '',
  });

  $scope.csr_state = {
    open: false,
  };

  $scope.gen_priv_key = function() {
    return $scope.file_resources.priv_key.$update().then(refreshPromise);
  }

  // TODO(nskelsey) this implementation for download and upload
  $scope.postFile = function(fileList, fileRes) {
    var file = fileList.item(0);
    FileReader.readAsText(file, $scope).then(function(str) {
      fileRes.content = str;
      return fileRes.$save();
    }).then(refreshPromise);
  };

  $scope.downloadFile = function(resource) {
     $http({
        method: 'GET',
        url: 'admin/config/tls/files/' + resource.name, // NOTE path
        responseType: 'blob',
     }).then(function (response) {
        var blob = response.data;
        FileSaver.saveAs(blob, resource.name + '.pem');
     });
  };

  $scope.iconClass = function(fileSum) {
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
    var delayProm = function() {
        var d = $q.defer();
        $window.setTimeout(function() { d.resolve(); }, delay);
        return d.promise;
    };

    for (var i = 0; i < num; i++) {
        p = p.then(f).then(delayProm);
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
    $scope.csr_state.tried = true;
    $http({
        method: 'POST',
        url: 'admin/config/tls/csr',
        responseType: 'blob',
        data: $scope.csr_cfg,
    }).then(function(response) {
      var blob = response.data;
      FileSaver.saveAs(blob, 'cert_sig_req.pem');
    });
  };
}]);
