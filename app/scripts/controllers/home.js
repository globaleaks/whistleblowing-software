'use strict';

GLClient.controller('HomeCtrl', ['$scope', '$location', 'Node', 'Authentication',
                    'WhistleblowerTip', 'Contexts', 'Receivers',
  function ($scope, $location, Node, Authentication, WhistleblowerTip, Contexts, Receivers) {
    $scope.receipt = '';
    $scope.configured = false;

    Node.get(function(node_info){
      $scope.node_info = node_info;
    });

    $scope.view_tip = function(receipt) {
      WhistleblowerTip(receipt, function(tip_id) {
        $location.path('/status/' + tip_id);
      });
    };

}]);
