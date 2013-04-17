'use strict';

GLClient.controller('HomeCtrl', ['$scope', '$location', 'Node', 'Authentication',
                    'WhistleblowerTip', 'Contexts', 'Receivers',
  function ($scope, $location, Node, Authentication, WhistleblowerTip, Contexts, Receivers) {
    $scope.receipt = '';
    $scope.configured = false;

    Node.get(function(node_info){
      $scope.node_info = node_info;
    });

    Receivers.query(function(receivers){
      if(receivers.length > 0) {
          $scope.receiver_configured = true;
      }
    });

    Contexts.query(function(contexts){
       if(contexts.length > 0) {
          $scope.context_configured = true;
          if($scope.receiver_configured == true) {
              $scope.configured = true;
          }
       }
    });

    $scope.view_tip = function(receipt) {
      WhistleblowerTip(receipt, function(tip_id) {
        $location.path('/status/' + tip_id);
      });
    };

}]);
