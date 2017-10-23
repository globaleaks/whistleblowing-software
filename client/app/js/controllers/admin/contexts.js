GLClient.controller('AdminContextsCtrl',
  ['$scope', 'Utils', 'AdminContextResource',
  function($scope, Utils, AdminContextResource) {

  $scope.save_context = function (context, cb) {
    var updated_context = new AdminContextResource(context);

    return Utils.update(updated_context, cb);
  };

  $scope.moveUpAndSave = function(elem) {
    Utils.moveUp(elem);
    $scope.save_context(elem);
  };

  $scope.moveDownAndSave = function(elem) {
    Utils.moveDown(elem);
    $scope.save_context(elem);
  };
}]).
controller('AdminContextEditorCtrl', ['$scope', '$http', 'Utils', 'AdminContextResource',
  function($scope, $http, Utils, AdminContextResource) {
  $scope.editing = false;

  $scope.toggleEditing = function () {
    $scope.editing = !$scope.editing;
  };

  $scope.moveUp = function(e, idx) { swap(e, idx, -1); };
  $scope.moveDown = function(e, idx) { swap(e, idx, 1); };

  function swap($event, index, n) {
    $event.stopPropagation();

    var target = index + n;
    if (target < 0 || target >= $scope.admin.contexts.length) {
      return;
    }

    $scope.admin.contexts[index] = $scope.admin.contexts[target];
    $scope.admin.contexts[target] = $scope.context;

    $http({
      method: 'PUT',
      url: '/admin/contexts',
      data: {
        'operation': 'order_elements',
        'args': {'ids': $scope.admin.contexts.map(function(c) { return c.id; })},
      },
    }).then(function() {
      $rootScope.successes.push({});
    });
  }

  function recAttachedToCtx(rec) {
    return $scope.context.receivers.indexOf(rec.id) > -1;
  }

  $scope.selected_receivers = $scope.admin.receivers.filter(recAttachedToCtx);
  $scope.potential_receivers = $scope.admin.receivers.filter(function(rec) {
    return !recAttachedToCtx(rec);
  });

  $scope.showSelect = false;
  $scope.toggleSelect = function() {
    $scope.showSelect = true;
  };

  $scope.toggle = function(receiver) {
    var idx = $scope.context.receivers.indexOf(receiver.id);
    if (idx === -1) {
      $scope.context.receivers.push(receiver.id);
    } else {
      $scope.context.receivers.splice(idx, 1);
    }

    $scope.editContext.$dirty = true;
    $scope.editContext.$pristine = false;
  };

  $scope.updateContextImgUrl = function() {
    $scope.contextImgUrl = '/admin/contexts/' + $scope.context.id + '/img#' + Utils.randomFluff();
  };

  $scope.updateContextImgUrl();

  $scope.tip_ttl_off = $scope.context.tip_timetolive === -1;
  $scope.$watch('context.tip_timetolive', function(new_val) {
    if (angular.isDefined(new_val)) {
      $scope.tip_ttl_off = new_val === -1;
    }
  });

  $scope.deleteContext = function() {
    Utils.deleteDialog($scope.context).then(function() {
      return Utils.deleteResource(AdminContextResource, $scope.admin.contexts, $scope.context);
    });
  };
}]).
controller('AdminContextReceiverSelectorCtrl', ['$scope', function($scope) {
  $scope.moveUp = function(idx) { swap(idx, -1); };
  $scope.moveDown = function(idx) { swap(idx, 1); };

  function swap(index, n) {
    var target = index + n;
    if (target > -1 && target < $scope.selected_receivers.length) {
      var tmp = $scope.selected_receivers[target];
      var tmpIdx = $scope.selected_receivers[index];
      $scope.selected_receivers[target] = tmpIdx;
      $scope.selected_receivers[index] = tmp;

      $scope.context.receivers = $scope.selected_receivers.map(function(r) { return r.id; });
    }
  }

  $scope.removeElem = function(rec, i) {
    $scope.selected_receivers.splice(i, 1);
    $scope.potential_receivers.push(rec);
    $scope.context.receivers = $scope.selected_receivers.map(function(r) { return r.id; });
  };
}]).
controller('AdminContextAddCtrl', ['$scope', function($scope) {
  $scope.new_context = {};

  $scope.add_context = function() {
    var context = new $scope.admin_utils.new_context();

    context.name = $scope.new_context.name;
    context.questionnaire_id = $scope.admin.node.default_questionnaire;
    context.presentation_order = $scope.newItemOrder($scope.admin.contexts, 'presentation_order');

    context.$save(function(new_context){
      $scope.admin.contexts.push(new_context);
      $scope.new_context = {};
    });
  };
}]);
