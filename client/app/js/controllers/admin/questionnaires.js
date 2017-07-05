GLClient.controller('AdminQuestionnaireCtrl',
  ['$scope', 'AdminQuestionnaireResource',
  function($scope, AdminQuestionnaireResource){
  $scope.tabs = [
    {
      title:"Questionnaire configuration",
      template:"views/admin/questionnaires/main.html"
    },
    {
      title:"Question templates",
      template:"views/admin/questionnaires/questions.html"
    }
  ];

  $scope.save_questionnaire = function(questionnaire, cb) {
    return $scope.Utils.update(questionnaire, cb);
  };

  $scope.delete_questionnaire = function(questionnaire) {
    AdminQuestionnaireResource.delete({
      id: questionnaire.id
    }, function(){
      var idx = $scope.admin.questionnaires.indexOf(questionnaire);
      $scope.admin.questionnaires.splice(idx, 1);
    });
  };
}]).
controller('AdminQuestionnaireEditorCtrl', ['$scope', 'AdminStepResource',
  function($scope, AdminStepResource) {

  $scope.editing = false;

  $scope.toggleEditing = function () {
    $scope.editing = !$scope.editing;
  };

  $scope.delStep = function(step) {
    AdminStepResource.delete({
      id: step.id
    }, function() {
      $scope.questionnaire.steps.splice($scope.questionnaire.steps.indexOf(step), 1);
    });
  };
}]).
controller('AdminQuestionnaireAddCtrl', ['$scope', function($scope) {
  $scope.new_questionnaire = {};

  $scope.add_questionnaire = function() {
    var questionnaire = new $scope.admin_utils.new_questionnaire();

    questionnaire.name = $scope.new_questionnaire.name;

    questionnaire.$save(function(new_questionnaire){
      $scope.admin.questionnaires.push(new_questionnaire);
      $scope.new_questionnaire = {};
    });
  };
}]);
