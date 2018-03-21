angular.module('GLDirectives', []).
  directive('textarea', function () {
    return {
      restrict: 'E',
      link: function postLink(scope, element, attrs) {
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
  directive('subdomainvalidator', function() {
    return {
      require: 'ngModel',
      link: function(scope, elem, attrs, ngModel) {
        ngModel.$parsers.unshift(function(viewValue) {
          viewValue = viewValue.toLowerCase();
          viewValue = viewValue.replace(/[^a-z0-9]/g,'');
          angular.element(elem).val(viewValue);
          return viewValue;
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
directive('singleErrorUpload', function() {
  return {
    restrict: 'A',
    controller: ['$scope', function($scope) {
       $scope.$watch('file_error_msgs.length', function() {
          // Reset the error display flag when a new error is pushed
          $scope.displayErr = true;
       });

       $scope.displayErr = true;
    }],
    templateUrl: 'views/partials/upload_error_msg.html',
  };
}).
directive('errorsUpload', function() {
  // Depends on file_error_msgs is defined in parent scope.
  return {
    restrict: 'A',
    templateUrl: 'views/partials/upload_error_msgs.html',
  };
}).
directive('extendFlowValidTypes', ['uploadUtils', function(uploadUtils) {
  return {
    restrict: 'A',
    scope: true,
    link: function(scope, iElment, iAttrs) {
      var validTypes = scope.$eval(iAttrs.extendFlowValidTypes);
      scope.$on('flow::fileAdded', function(event, _, flowFile) {

        if (!uploadUtils.validFilename(flowFile.name, validTypes)) {
          if (scope.file_error_msgs === undefined) scope.file_error_msgs = [];
          var errMsg = uploadUtils.translateInvalidTypeErr(flowFile.name, validTypes);
          scope.file_error_msgs.push(errMsg);
          event.preventDefault();
        }
      });
    },
  };
}]).
directive('extendFlowValidSize', ['uploadUtils', function(uploadUtils) {
  return {
    restrict: 'A',
    scope: true,
    link: function(scope, iElment, iAttrs) {
      var validSize = parseInt(scope.$eval(iAttrs.extendFlowValidSize));
      scope.$on('flow::fileAdded', function(event, _, flowFile) {
        if (flowFile.size > validSize) {
          if (scope.file_error_msgs == undefined) scope.file_error_msgs = [];
          var errMsg = uploadUtils.translateInvalidSizeErr(flowFile.name, validSize);
          scope.file_error_msgs.push(errMsg);
          event.preventDefault();
        }
      });
    }
  };
}]).
directive('imageUpload', function () {
  return {
    restrict: 'A',
    scope: {
      imageUploadModel: '=',
      imageUploadModelAttr: '@',
      imageUploadUrl: '@'
    },
    templateUrl: 'views/partials/image_upload.html',
    controller: 'ImageUploadCtrl'
  };
}).
// pgpPubKeyDisplay displays the important details from a public key.
directive('pgpPubkeyDisplay', ['$q', 'pgp', 'glbcKeyLib', function($q, pgp, glbcKeyLib) {
  // Create object that displays relevant key details to the user. This function
  // returns fingerprint, key id, creation date, and expiration date. If the parse
  // fails the function returns undefined.
  function pgpKeyDetails(armoredText) {
    var defer = $q.defer();

    if (typeof armoredText !== 'string') {
      return defer.reject();
    }

    if (typeof armoredText !== 'string' || armoredText.substr(0,3) !== '---') {
      return defer.reject();
    }

    // Catch the obivous errors and save time!
    if (typeof armoredText !== 'string' || armoredText.substr(0,3) !== '---') {
      return defer.reject();
    }

    var res = pgp.key.readArmored(armoredText);

    if (angular.isDefined(res.err)) {
      // There were errors. Bail out.
      return defer.reject();
    }

    var key = res.keys[0];

    var niceprint = niceFingerPrint(key.primaryKey.fingerprint);
    var uids = extractAllUids(key);
    var created = key.primaryKey.created;

    key.getExpirationTime().then(function(keyExpirationTime) {
      return defer.resolve({
        user_info: uids,
        fingerprint: niceprint,
        created: created,
        expiration: keyExpirationTime,
      });
    });

    return defer.promise;
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
    link: function(scope) {
      scope.$watch('keyStr', function(newVal) {
        if (!newVal) {
          return;
        }

        glbcKeyLib.validPublicKey(newVal).then(function(result) {
          if (result) {
            pgpKeyDetails(newVal).then(function(result) {
              if (result) {
                scope.key_details = result;
              }
            });
          }
        });
      });
    },
  };
}]).
// pgpPubkeyValidator binds to text-areas to provide input validation on user
// input PGP public keys. Note that the directive attaches itself to the
// containing form's ngModelController NOT the ngModel bound to the value of the
// text-area itself. If the key word 'canBeEmpty' the pgp key validator is disabled
// when the textarea's input is empty.
directive('pgpPubkeyValidator', ['$q', 'glbcKeyLib', function($q, glbcKeyLib) {
  // scope is the directives scope
  // elem is a jqlite reference to the bound element
  // attrs is the list of directives on the element
  // ngModel is the model controller attached to the form
  function link(scope, elem, attrs, ngModel) {
    scope.canBeEmpty = scope.pgpPubkeyValidator === 'canBeEmpty';

    // modelValue is the models value, viewVal is displayed on the page.
    ngModel.$asyncValidators.pgpPubKeyValidator = function(modelVal) {
      // Check for obvious problems.
      if (typeof modelVal !== 'string') {
        modelVal = '';
      }

      if (scope.canBeEmpty && modelVal === '') {
        return $q.resolve(true);
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
directive('singleClick', [function() {
  return {
    restrict: 'A',
    link: function(scope, elm) {
      elm.on('click', function() {
        elm.attr('disabled', true);
      });
    },
  };
}]).
directive('wbfile', [function() {
  return {
    restrict: 'A',
    scope: false,
    templateUrl: 'views/partials/wbfile.html',
  };
}]).
directive('filePickerInput', function() {
  return {
    restrict: 'A',
    templateUrl: 'views/partials/file_picker_input.html',
    scope: {
      filePickerInput: '&',
      labelText: '@',
    },
    link: function (scope, iElement) {
      iElement.find('input').on('change', function (event) {
	if(event.target.files && event.target.files.length > 0) {
          scope.$apply(function(){
            scope.filePickerInput({file: event.target.files[0]});
          });
        }
      });
    },
  };
}).
directive('requiredAsterisk', function() {
  return {
    restrict: 'A',
    templateUrl: 'views/partials/required_asterisk.html',
  }
}).
directive('releaseMsg', function() {
  return {
    restrict: 'A',
    templateUrl: 'views/admin/home/releasemsg.html',
  };
}).
directive('isolateClick', function() {
  return {
    link: function(scope, elem) {
      elem.on('click', function(e){
        e.stopPropagation();
      });
    }
 };
});
