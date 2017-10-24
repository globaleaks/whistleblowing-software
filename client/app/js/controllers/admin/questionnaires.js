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

    return Utils.update(updated_questionnaire, cb);
  };

  $scope.delete_questionnaire = function(questionnaire) {
    return Utils.deleteResource(AdminQuestionnaireResource, $scope.admin.questionnaires, questionnaire);
  };
}]).
controller('AdminQuestionnaireEditorCtrl', ['$scope', '$http', 'Utils', 'FileSaver', 'AdminStepResource',
  function($scope, $http, Utils, FileSaver, AdminStepResource) {

  $scope.editing = false;

  $scope.toggleEditing = function () {
    $scope.editing = !$scope.editing;
  };

  $scope.delStep = function(step) {
    return Utils.deleteResource(AdminStepResource, $scope.questionnaire.steps, step);
  };

  $scope.exportQuestionnaire = function(obj) {
    $http({
      method: 'GET',
      url: 'admin/questionnaires/' + obj.id,
      responseType: 'blob',
    }).then(function (response) {
      FileSaver.saveAs(response.data, obj.name + '.json');
    });
  };
}]).
controller('AdminQuestionnaireAddCtrl', ['$scope', '$http', 'Utils', 'AdminQuestionnaireResource',
  function($scope, $http, Utils, AdminQuestionnaireResource) {
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
    Utils.readFileAsText(file).then(function(txt) {
      return $http({
        method: 'POST',
        url: 'admin/questionnaires?multilang=1',
        data: txt,
      })
    }).then(function(resp) {
      var new_q = new AdminQuestionnaireResource(resp.data);
      $scope.admin.questionnaires.push(new_q);
    }, Utils.displayErrorMsg);
  };

}]);
