GL.controller("AdminQuestionnaireCtrl",
  ["$scope", "$http", "AdminQuestionnaireResource",
  function($scope, $http, AdminQuestionnaireResource){
  $scope.tabs = [
    {
      title:"Questionnaires",
      template:"views/admin/questionnaires/main.html"
    },
    {
      title:"Question templates",
      template:"views/admin/questionnaires/questions.html"
    }
  ];

  $scope.deleted_fields_ids = [];

  $scope.showAddQuestionnaire = false;
  $scope.toggleAddQuestionnaire = function() {
    $scope.showAddQuestionnaire = !$scope.showAddQuestionnaire;
  };

  $scope.showAddQuestion = false;
  $scope.toggleAddQuestion = function() {
    $scope.showAddQuestion = !$scope.showAddQuestion;
  };

  $scope.importQuestionnaire = function(file) {
    $scope.Utils.readFileAsText(file).then(function(txt) {
      return $http({
        method: "POST",
        url: "api/admin/questionnaires?multilang=1",
        data: txt,
      });
    }).then(function() {
       $scope.reload();
    }, $scope.Utils.displayErrorMsg);
  };

  $scope.save_questionnaire = function(questionnaire, cb) {
    var updated_questionnaire = new AdminQuestionnaireResource(questionnaire);

    return $scope.Utils.update(updated_questionnaire, cb);
  };

  $scope.delete_questionnaire = function(questionnaire) {
    $scope.Utils.deleteDialog().then(function() {
      return $scope.Utils.deleteResource(AdminQuestionnaireResource, $scope.resources.questionnaires, questionnaire);
    });
  };
}]).
controller("AdminQuestionnaireEditorCtrl", ["$scope", "$uibModal", "$http", "AdminStepResource",
  function($scope, $uibModal, $http, AdminStepResource) {

  $scope.editing = false;

  $scope.toggleEditing = function () {
    $scope.editing = $scope.questionnaire.editable && !$scope.editing;
  };

  $scope.showAddStep = false;
  $scope.toggleAddStep = function() {
    $scope.showAddStep = !$scope.showAddStep;
  };

  $scope.parsedFields = $scope.fieldUtilities.parseQuestionnaire($scope.questionnaire, {});

  $scope.delStep = function(step) {
    $scope.Utils.deleteDialog().then(function() {
      return $scope.Utils.deleteResource(AdminStepResource, $scope.questionnaire.steps, step);
    });
  };

  $scope.duplicate_questionnaire = function(questionnaire) {
    $uibModal.open({
      templateUrl: "views/modals/questionnaire_duplication.html",
      controller: "QuestionaireOperationsCtrl",
      resolve: {
        questionnaire: function () {
          return questionnaire;
        },
        operation: function () {
          return "duplicate";
        }
      }
    });
  };

  $scope.exportQuestionnaire = function(obj) {
    return $scope.Utils.saveAs(obj.name + ".json", "api/admin/questionnaires/" + obj.id);
  };
}]).
controller("AdminQuestionnaireAddCtrl", ["$scope", function($scope) {
  $scope.new_questionnaire = {};

  $scope.add_questionnaire = function() {
    var questionnaire = new $scope.AdminUtils.new_questionnaire();

    questionnaire.name = $scope.new_questionnaire.name;

    questionnaire.$save(function(new_questionnaire){
      $scope.resources.questionnaires.push(new_questionnaire);
      $scope.new_questionnaire = {};
    });
  };
}]).
controller("QuestionaireOperationsCtrl",
  ["$scope", "$http", "$location", "$uibModalInstance", "questionnaire", "operation",
   function ($scope, $http, $location, $uibModalInstance, questionnaire, operation) {
  $scope.questionnaire = questionnaire;
  $scope.operation = operation;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.confirm = function () {
    $uibModalInstance.close();

    if ($scope.operation === "duplicate") {
      $http.post(
        "api/admin/questionnaires/duplicate",
        {
          questionnaire_id: $scope.questionnaire.id,
          new_name: $scope.duplicate_questionnaire.name
        }
      ).then(function () {
        $scope.reload();
      });
    }
  };
}]);
