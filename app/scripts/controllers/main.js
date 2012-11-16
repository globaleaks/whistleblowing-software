'use strict';

GLClient.controller('MainCtrl', ['$scope', 'Node',
    function($scope, Node) {

  // We set this to the parent scope that that we don't have to make this
  // request again later.
  $scope.$parent.node_info = Node.info(function(){
    $scope.$parent.selected_language = $scope.node_info.available_languages[0].code;
    $scope.$parent.node_name = function() {
      return $scope.$parent.node_info.name[$scope.selected_language];
    }
  });
}]);
