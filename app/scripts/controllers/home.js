'use strict';

GLClient.controller('HomeCtrl', ['$scope', '$location', 'Node', 'Authentication',
                    'WhistleblowerTip', 'Contexts',
  function ($scope, $location, Node, Authentication, WhistleblowerTip, Contexts) {
    $scope.receipt = '';
    $scope.configured = false;

    Node.get(function(node_info){
      $scope.node_info = node_info;
    });


    Contexts.query(function(contexts){
      if(contexts.length > 0) {
          $scope.configured = true
      }
    });

    $scope.view_tip = function(receipt) {
      WhistleblowerTip(receipt, function(tip_id) {
        $location.path('/status/' + tip_id);
      });
    };

}]);
