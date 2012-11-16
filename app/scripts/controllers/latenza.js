'use strict';

GLClient.controller('LatenzaCtrl', 
    ['$scope', '$timeout', 'Node',
    function($scope, $timeout, Node) {

  $scope.loading = false;

  // We do this in latenza so that we don't have to do requests multiple
  // times.
  if (!$scope.node_info) {
    // We set this to the parent scope that that we don't have to make this
    // request again later.
    $scope.$parent.node_info = Node.info(function() {
      console.log($scope.node_info);
      // Here are functions that are specific to language localization. They
      // are somwhat hackish and I am sure there is a javascript ninja way of
      // doing them.
      // XXX refactor these into something more 1337
      $scope.$parent.selected_language =
        $scope.node_info.available_languages[0].code;

      $scope.$parent.get_node_name = function() {
        return $scope.$parent.node_info.name[$scope.selected_language];
      }

      // Here we add to every context a special function that allows us to
      // retrieve the value of the name and description of the context
      // geolocalized.
      for (var i in $scope.$parent.node_info.contexts) {
        $scope.$parent.node_info.contexts[i].get_context_name = function() {
          return this.name[$scope.selected_language];
        }
        $scope.$parent.node_info.contexts[i].get_context_description = function() {
          return this.description[$scope.selected_language];
        }
      }
    });
  }

}]);
