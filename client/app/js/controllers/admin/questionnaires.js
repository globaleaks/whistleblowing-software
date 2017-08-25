GLClient.controller('AdminQuestionnaireCtrl',
  ['$scope', 'Utils', 'AdminQuestionnaireResource',
  function($scope, Utils, AdminQuestionnaireResource){
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

  $scope.admin.get_field_attrs = function(type) {
    if (type in $scope.admin.field_attrs) {
      return $scope.admin.field_attrs[type];
    } else {
      return {};
    }
  };

  $scope.save_questionnaire = function(questionnaire, cb) {
    var updated_questionnaire = new AdminQuestionnaireResource(questionnaire);

    return $scope.Utils.update(updated_questionnaire, cb);
  };

  $scope.delete_questionnaire = function(questionnaire) {
    AdminQuestionnaireResource.delete({
      id: questionnaire.id
    }, function(){
      var idx = $scope.admin.questionnaires.indexOf(questionnaire);
      $scope.admin.questionnaires.splice(idx, 1);
    });
  };

  $scope.importQuestionnaire = function(file) {
    Utils.readFileAsJson(file).then(function(obj) {
      var questionnaire = new AdminQuestionnaireResource(obj);
      return questionnaire.$save({full: '1'}).$promise;
    }).then(function(new_q) {
      $scope.admin.questionnaire.push(new_q);
    }, Utils.displayErrorMsg);
  };
}]).
controller('AdminQuestionnaireEditorCtrl', ['$scope', '$http', 'FileSaver', 'AdminStepResource',
  function($scope, $http, FileSaver, AdminStepResource) {

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

  $scope.downloadQuestionnaire = function(obj) {
    $http({
      method: 'GET',
      url: 'admin/questionnaires/' + obj.id,
      responseType: 'blob',
    }).then(function (response) {
      FileSaver.saveAs(response.data, obj.name + '.json');
    });
  };
}]).
controller('AdminQuestionnaireAddCtrl', ['$scope', 'Utils', 'AdminQuestionnaireResource', function($scope, Utils, AdminQuestionnaireResource) {
  $scope.new_questionnaire = {};

  $scope.add_questionnaire = function() {
    var questionnaire = new $scope.admin_utils.new_questionnaire();

    questionnaire.name = $scope.new_questionnaire.name;

    questionnaire.$save(function(new_questionnaire){
      $scope.admin.questionnaires.push(new_questionnaire);
      $scope.new_questionnaire = {};
    });
  };

  $scope.importQuestionnaire = function(file) {
    Utils.readFileAsJson(file).then(function(obj) {
        var questionnaire = new AdminQuestionnaireResource(obj);

        return questionnaire.$save().$promise;
    }).then(function(new_q) {
      $scope.admin.questionnaire.push(new_q);
    }, function(err) {
      Utils.displayErrorMsg(err);
    });
  };
}]);
