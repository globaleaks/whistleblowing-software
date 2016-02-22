GLClient.controller('AdminQuestionnaireCtrl', ['$scope', '$uibModal',
                    function($scope, $uibModal){
  $scope.tabs = [
    {
      title:"Questionnaire configuration",
      template:"views/admin/questionnaires/main.html",
      ctrl: TabCtrl
    },
    {
      title:"Question templates",
      template:"views/admin/questionnaires/questions.html",
      ctrl: TabCtrl
    }
  ];
}]);

GLClient.controller('AdminQuestionnairesCtrl',
  ['$scope', 'AdminQuestionnaireResource',
  function($scope, AdminQuestionnaireResource) {

  $scope.save_questionnaire = function(questionnaire, cb) {
    alert(123);
    var updated_questionnaire = new AdminQuestionnaireResource(questionnaire);

    return $scope.update(updated_questionnaire, cb);
  };

  $scope.delete_questionnaire = function(questionnaire) {
    AdminQuestionnaireResource['delete']({
      id: questionnaire.id
    }, function(){
      var idx = $scope.admin.questionnaires.indexOf(questionnaire);
      $scope.admin.questionnaires.splice(idx, 1);
    });
  };
}]);

GLClient.controller('AdminQuestionnaireEditorCtrl', ['$scope', 'AdminStepResource',
  function($scope, AdminStepResource) {

  $scope.editing = false;

  $scope.toggleEditing = function () {
    $scope.editing = !$scope.editing;
  };

  $scope.delStep = function(step) {
    AdminStepResource['delete']({
      id: step.id
    }, function() {
      $scope.questionnaire.steps.splice($scope.questionnaire.steps.indexOf(step), 1);
    });
  };

  $scope.delAllSteps = function() {
    angular.forEach($scope.questionnaire.steps, function(step) {
      $scope.delStep(step);
    });
  };
}]);

GLClient.controller('AdminQuestionnaireAddCtrl', ['$scope', function($scope) {
  $scope.new_questionnaire = {};

  $scope.add_questionnaire = function() {
    var questionnaire = new $scope.admin.new_questionnaire();

    questionnaire.name = $scope.new_questionnaire.name;

    questionnaire.$save(function(new_questionnaire){
      $scope.admin.questionnaires.push(new_questionnaire);
      $scope.new_questionnaire = {};
    });
  };

}]);
