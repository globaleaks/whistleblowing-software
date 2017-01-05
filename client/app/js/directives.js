angular.module('GLDirectives', []).
  directive('textarea', function () {
    return {
      restrict: 'E',
      link: function postLink(scope, element, attrs) {
        // hidding the scroll of textarea
        element.css('overflow', 'hidden');
        element.css('min-height', '2em');

        var update = function(){
          element.css("height", "auto");

          var height = element[0].scrollHeight;
          if(height > 0){
            element.css("height", height + "px");
          }
        };

        scope.$watch(attrs.ngModel, function(){
          update();
        });

        attrs.$set("ngTrim", "false");
      }
    };
}).
  directive('inputPrefix', function() {
    return {
      require: 'ngModel',
      link: function(scope, elem, attrs, ngModel) {
        function inputPrefix(value) {
          var prefix = attrs.prefix;

          var result = prefix;

          if (value.length >= prefix.length) {
            if (value.slice(0, prefix.length) !== prefix) {
              result = prefix + value;
            } else {
              result = value;
            }
          }

          ngModel.$setViewValue(result);
          ngModel.$render();

          return result;
        }

        ngModel.$formatters.push(inputPrefix);
        ngModel.$parsers.push(inputPrefix);
      }
    };
}).
  directive('keycodevalidator', function() {
    return {
      require: 'ngModel',
      link: function(scope, elem, attrs, ngModel) {
        ngModel.$setValidity('keycodevalidator', false);
        ngModel.$parsers.unshift(function(viewValue) {
          var result = '';
          ngModel.$setValidity('keycodevalidator', false);
          viewValue = viewValue.replace(/\D/g,'');
          while (viewValue.length > 0) {
            result += viewValue.substring(0, 4);
            if(viewValue.length >= 4) {
              if (result.length < 19) {
                result += ' ';
              }
              viewValue = viewValue.substring(4);
            } else {
              break;
            }
          }
          angular.element(elem).val(result);
          if (result.length === 19) {
            ngModel.$setValidity('keycodevalidator', true);
          }
          return result;
        });
      }
    };
}).
 directive("fileread", function () {
   return {
     scope: {
       fileread: "="
     },
     /* eslint-disable no-unused-vars */
     link: function (scope, element, attributes) {
     /* eslint-enable no-unused-vars */
       element.bind('click', function(){
         element.val('');
       });

       element.bind("change", function (changeEvent) {
         var reader = new FileReader();
         reader.onload = function (e) {
           scope.$apply(function () {
             scope.fileread(e.target.result);
           });
         };
         reader.readAsText(changeEvent.target.files[0]);
       });
     }
   };
}).
directive('zxPasswordMeter', function() {
  return {
    scope: {
      value: "="
    },
    templateUrl: "views/partials/password_meter.html",
    link: function(scope) {
      scope.type = null;
      scope.text = '';

      scope.$watch('value', function(newValue) {
        if (newValue === undefined) {
          return;
        }

        if (newValue.password === 'undefined') { // <- intentionally as string
          // Short term fix for:
          // https://github.com/ghostbar/angular-zxcvbn/issues/13
          newValue.password = '';
        }

        if (newValue.password === '') {
          scope.type = null;
          scope.text = '';
        } else if (newValue.score < 3) {
          newValue.score = 1;
          scope.type = 'danger';
          scope.text = 'Weak';
        } else if (newValue.score < 4) {
          // guesses needed >= 10^8, <= 10^10
          scope.type = 'warning';
          scope.text = 'Acceptable';
        } else {
          // guesses needed >= 10^10
          scope.type = 'success';
          scope.text = 'Strong';
        }
      });
    }
  };
}).
directive('inlineUploadError', function() {
  return {
    restrict: 'A',
    template: '<span data-ng-if="file_error_msg" class="text-danger"><span data-translate>Error:</span> <span>{{file_error_msg}}</span></span>',
  };
}).
directive('extendFlowValidTypes', ['uploadUtils', function(uploadUtils) {
  return {
    restrict: 'A',
    scope: true,
    link: function(scope, iElment, iAttrs, ctrl) {
      var validTypes = scope.$eval(iAttrs.extendFlowValidTypes);
      scope.$on('flow::fileAdded', function(event, _, flowFile) {
        if (!uploadUtils.validFilename(flowFile.name, validTypes)) {
          scope.file_error_msg = "The submitted files must end in the one of the following extensions: " + validTypes;
          event.preventDefault();
        }
      });
    },
  };
}]).
directive('imageUpload', function () {
  return {
    restrict: 'A',
    scope: {
      nodeModel: '=',
      imageUploadModel: '=',
      imageUploadModelAttr: '@',
      imageUploadUrl: '@'
    },
    templateUrl: 'views/partials/image_upload.html',
    controller: 'ImageUploadCtrl'
  };
}).
// pgpPubKeyDisplay displays the important details from a public key.
directive('pgpPubkeyDisplay', ['pgp', 'glbcKeyLib', function(pgp, glbcKeyLib) {
  // Create object that displays relevant key details to the user. This function
  // returns fingerprint, key id, creation date, and expiration date. If the parse
  // fails the function returns undefined.
  function pgpKeyDetails(armoredText) {
    if (typeof armoredText !== 'string') {
      return;
    }

    if (typeof armoredText !== 'string' || armoredText.substr(0,3) !== '---') {
      return;
    }

    // Catch the obivous errors and save time!
    if (typeof armoredText !== 'string' || armoredText.substr(0,3) !== '---') {
      return;
    }

    var res = pgp.key.readArmored(armoredText);

    if (angular.isDefined(res.err)) {
      // There were errors. Bail out.
      return;
    }

    var key = res.keys[0];

    var niceprint = niceFingerPrint(key.primaryKey.fingerprint);
    var uids = extractAllUids(key);
    var created = key.primaryKey.created;

    return {
      user_info: uids,
      fingerprint: niceprint,
      created: created,
      expiration: key.getExpirationTime(),
    };
  }

  // niceFingerPrint produces the full key fingerprint in the standard
  // 160 bit format. See: https://tools.ietf.org/html/rfc4880#section-12.2
  function niceFingerPrint(print) {
    if (typeof print !== 'string' && print.length !== 40) {
      // Do nothing, the passed params are strange.
      return print;
    }

    print = print.toUpperCase();

    var nice = print[0];
    for (var i = 1; i < 40; i++) {
      // Insert a space every 4th octet
      if (i % 4 === 0) {
        nice += " ";
      }
      if (i % 20 === 0) {
        nice += " ";
      }
      nice += print[i];
    }

    return nice;
  }

  // Returns all of the userId's found in the list of uids attached to the key.
  function extractAllUids(key) {
    var uids = [];
    key.users.forEach(function(user) {
      uids.push(user.userId.userid);
    });
    return uids;
  }

  return {
    restrict: 'A',
    templateUrl: 'views/partials/pubkey_display.html',
    scope: {
      keyStr: '=keyStr',

    },
    controller: ['$scope', function($scope) {
      $scope.$watch('keyStr', function(newVal) {
        if (newVal === "") {
          return;
        }
        $scope.is_valid_key = glbcKeyLib.validPublicKey(newVal);
        if ($scope.is_valid_key) {
          $scope.key_details = pgpKeyDetails(newVal);
        }
      });
  }]};
}]).
// pgpPubkeyValidator binds to text-areas to provide input validation on user
// input PGP public keys. Note that the directive attaches itself to the
// containing form's ngModelController NOT the ngModel bound to the value of the
// text-area itself. If the key word 'canBeEmpty' the pgp key validator is disabled
// when the textarea's input is empty.
directive('pgpPubkeyValidator', ['glbcKeyLib', function(glbcKeyLib) {
  // scope is the directives scope
  // elem is a jqlite reference to the bound element
  // attrs is the list of directives on the element
  // ngModel is the model controller attached to the form
  function link(scope, elem, attrs, ngModel) {

    scope.canBeEmpty = scope.pgpPubkeyValidator === 'canBeEmpty';

    // modelValue is the models value, viewVal is displayed on the page.
    ngModel.$validators.pgpPubKeyValidator = function(modelVal) {
      // Check for obvious problems.
      if (typeof modelVal !== 'string') {
        modelVal = '';
      }

      if (scope.canBeEmpty && modelVal === '') {
        return true;
      }

      return glbcKeyLib.validPublicKey(modelVal);
    };
  }
  // Return a Directive Definition Object for angular to compile
  return {
    restrict: 'A',
    require: 'ngModel',
    link: link,
    scope: {
      // The string passed to the directive is used to assign special key word behavior.
      pgpPubkeyValidator: '@',
    }
  };
}]).
directive('stopccp', function(){
  return {
    link:function(scope,element){
      element.on('cut copy paste', function (event) {
        event.preventDefault();
      });
    }
  };
}).
// isolateForm directive makes possible to isolate validation of nested forms
directive('isolateForm', [function () {
  return {
    restrict: 'A',
    require: '?form',
    link: function (scope, elm, attrs, ctrl) {
      if (!ctrl) {
        return;
      }

      // Do a copy of the controller
      var ctrlCopy = {};
      angular.copy(ctrl, ctrlCopy);

      // Get the parent of the form
      var parent = elm.parent().controller('form');
      // Remove parent link to the controller
      parent.$removeControl(ctrl);

      // Replace form controller with a "isolated form"
      var isolatedFormCtrl = {
        $setValidity: function (validationToken, isValid, control) {
          ctrlCopy.$setValidity(validationToken, isValid, control);
          parent.$setValidity(validationToken, true, ctrl);
        },
        $setDirty: function () {
          elm.removeClass('ng-pristine').addClass('ng-dirty');
          ctrl.$dirty = true;
          ctrl.$pristine = false;
        },
      };

      angular.extend(ctrl, isolatedFormCtrl);
    }
  };
}])
.directive('singleClick', [function() {
  return {
    restrict: 'A',
    link: function(scope, elm) {
      elm.on('click', function() {
        elm.attr('disabled', true);
      });
    },
  };
}])
.directive('wbfile', [function() {
  return {
    restrict: 'A',
    scope: false,
    templateUrl: 'views/partials/wbfile.html',
  };
}]);
