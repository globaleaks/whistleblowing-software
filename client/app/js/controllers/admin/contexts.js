GL.controller("AdminContextsCtrl",
  ["$scope", "AdminContextResource",
  function($scope, AdminContextResource) {
  $scope.admin_receivers_by_id = $scope.Utils.array_to_map($scope.resources.users);

  $scope.save_context = function (context, cb) {
    if (context.additional_questionnaire_id === null) {
      context.additional_questionnaire_id = "";
    }

    var updated_context = new AdminContextResource(context);

    return $scope.Utils.update(updated_context, cb);
  };

  $scope.showAddContext = false;
  $scope.toggleAddContext = function() {
    $scope.showAddContext = !$scope.showAddContext;
  };

  $scope.moveUpAndSave = function(elem) {
    $scope.Utils.moveUp(elem);
    $scope.save_context(elem);
  };

  $scope.moveDownAndSave = function(elem) {
    $scope.Utils.moveDown(elem);
    $scope.save_context(elem);
  };
}]).
controller("AdminContextEditorCtrl", ["$scope", "$http", "AdminContextResource",
  function($scope, $http, AdminContextResource) {
  $scope.editing = false;

  $scope.toggleEditing = function () {
    $scope.editing = !$scope.editing;
  };

  $scope.onReminderSoftChanged = function() {
    if ($scope.context.tip_reminder_soft > $scope.context.tip_reminder_hard){
      $scope.context.tip_reminder_hard = $scope.context.tip_reminder_soft;
    }
  };

  $scope.onReminderHardChanged = function() {
    if ($scope.context.tip_reminder_hard === 0){
      $scope.context.tip_reminder_soft = 0;
    }else if ($scope.context.tip_reminder_hard < $scope.context.tip_reminder_soft){
      $scope.context.tip_reminder_soft = $scope.context.tip_reminder_hard;
    }
  };

  function swap($event, index, n) {
    $event.stopPropagation();

    var target = index + n;
    if (target < 0 || target >= $scope.resources.contexts.length) {
      return;
    }

    $scope.resources.contexts[index] = $scope.resources.contexts[target];
    $scope.resources.contexts[target] = $scope.context;

    return $http({
      method: "PUT",
      url: "api/admin/contexts",
      data: {
        "operation": "order_elements",
        "args": {"ids": $scope.resources.contexts.map(function(c) { return c.id; })},
      },
    });
  }

  $scope.moveUp = function(e, idx) { swap(e, idx, -1); };
  $scope.moveDown = function(e, idx) { swap(e, idx, 1); };

  $scope.showSelect = false;
  $scope.toggleSelect = function() {
    $scope.showSelect = true;
  };

  $scope.moveReceiver = function(rec) {
    $scope.context.receivers.push(rec.id);
    $scope.showSelect = false;
  };

  $scope.receiverNotSelectedFilter = function(item) {
    return $scope.context.receivers.indexOf(item.id) === -1;
  };

  $scope.deleteContext = function() {
    $scope.Utils.deleteDialog().then(function() {
      return $scope.Utils.deleteResource(AdminContextResource, $scope.resources.contexts, $scope.context);
    });
  };
}]).
controller("AdminContextReceiverSelectorCtrl", ["$scope", function($scope) {
  function swap(index, n) {
    var target = index + n;
    if (target > -1 && target < $scope.context.receivers.length) {
      var tmp = $scope.context.receivers[target];
      var tmpIdx = $scope.context.receivers[index];
      $scope.context.receivers[target] = tmpIdx;
      $scope.context.receivers[index] = tmp;
    }
  }

  $scope.moveUp = function(idx) { swap(idx, -1); };
  $scope.moveDown = function(idx) { swap(idx, 1); };
}]).
controller("AdminContextAddCtrl", ["$scope", function($scope) {
  $scope.new_context = {};

  $scope.add_context = function() {
    var context = new $scope.AdminUtils.new_context();

    context.name = $scope.new_context.name;
    context.questionnaire_id = $scope.resources.node.default_questionnaire;
    context.order = $scope.newItemOrder($scope.resources.contexts, "order");

    context.$save(function(new_context){
      $scope.resources.contexts.push(new_context);
      $scope.new_context = {};
    });
  };
}]);
