GLClient.controller('SubmissionCtrl', ['$scope', 
    '$http', 'Node', 'Submission', function($scope, $http, Node, Submission) {
  Node.info_node().
    success(function(data) {
      // XXX add sanitization and validation
      var parsed_data = data;
      $scope.name = parsed_data['name'];
      $scope.statistics = parsed_data['statistics'];
      $scope.node_properties = parsed_data['node_properties'];

      // We use the scope variable uploaded_files to keep track of the files
      // that are uploaded.
      $scope.uploaded_files = [];

      // XXX
      // We key the contexts dict to their context_gus
      // Perhaps its worthwhile to change the API in light of this.
      $scope.contexts = {}
      for (i in parsed_data['contexts']) {
        var context = parsed_data['contexts'][i];
        $scope.contexts[context.context_gus] = context;
      }

      $scope.current_context_gus = parsed_data['contexts'][0].context_gus;
      $scope.description = parsed_data['description'];
      $scope.public_site = parsed_data['public_site'];
      $scope.hidden_service = parsed_data['hidden_service'];
      $scope.url_schema = parsed_data['url_schema'];

      // XXX this is somewhat hackish. There is probably a more angular way of
      // doing it
      $scope.get_current_context = function(){
        return $scope.contexts[$scope.current_context_gus];
      }

      $scope.create_submission = function(){
        Submission.new_submission($scope.current_context_gus).success(
            function(data){
          $scope.submission_gus = data['submission_gus'];
        });
      }

      $scope.submit = function() {

      }

      // XXX this needs refactoring.
      Submission.new_submission($scope.current_context_gus).success(
          function(data){
        $scope.submission_gus = data['submission_gus'];
      });


    }).
    error(function(data, status, headers, config) {
      $scope.error = {'error': 'node info error'};
    });
}]);
