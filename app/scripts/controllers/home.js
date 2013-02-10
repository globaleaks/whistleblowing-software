'use strict';

GLClient.controller('HomeCtrl', ['$scope', 'Node',
  function($scope, Node) {
    Node.get(function(node_info){
      $scope.node_info = node_info;
    });
}]);
