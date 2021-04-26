GL.directive("dynamicTextarea", function () {
  return {
    restrict: "A",
    link: function postLink(scope, element, attrs) {
      element.css("min-height", "2rem");

      var update = function(){
        element.css("height", "auto");

        var height = element[0].scrollHeight;
        if(height){
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
directive("receiptvalidator", function() {
  return {
    require: "ngModel",
    link: function(scope, elem, attrs, ngModel) {
      ngModel.$setValidity("receiptvalidator", false);
      ngModel.$parsers.unshift(function(viewValue) {
        var result = "";

        ngModel.$setValidity("receiptvalidator", false);
        viewValue = viewValue.replace(/\D/g, "");

        while (viewValue.length) {
          result += viewValue.substring(0, 4);
          if(viewValue.length >= 4) {
            if (result.length < 19) {
              result += " ";
            }
            viewValue = viewValue.substring(4);
          } else {
            break;
          }
        }

        angular.element(elem).val(result);

        if (result.length === 19) {
          ngModel.$setValidity("receiptvalidator", true);
        }

        return result;
      });
    }
  };
}).
directive("recoverykeyvalidator", function() {
  return {
    require: "ngModel",
    link: function(scope, elem, attrs, ngModel) {
      ngModel.$setValidity("recoverykeyvalidator", false);
      ngModel.$parsers.unshift(function(viewValue) {
        var result = "";

        ngModel.$setValidity("recoverykeyvalidator", false);
        viewValue = viewValue.replace(/[^[a-zA-Z0-9]/g, "").toUpperCase();

        while (viewValue.length) {
          result += viewValue.substring(0, 4);
          if(viewValue.length >= 4) {
            if (result.length < 64) {
              result += "-";
            }
            viewValue = viewValue.substring(4);
          } else {
            break;
          }
        }

        angular.element(elem).val(result);

        if (result.length === 64) {
          ngModel.$setValidity("recoverykeyvalidator", true);
        }

        return result;
      });
    }
  };
}).
directive("subdomainvalidator", function() {
  return {
    require: "ngModel",
    link: function(scope, elem, attrs, ngModel) {
      ngModel.$parsers.unshift(function(viewValue) {
        viewValue = viewValue.toLowerCase();
        viewValue = viewValue.replace(/[^a-z0-9-]/g,"");
        angular.element(elem).val(viewValue);
        return viewValue;
      });
    }
  };
}).
directive("passwordMeter", function() {
  return {
    scope: {
      value: "="
    },
    templateUrl: "views/partials/password_meter.html",
    link: function(scope) {
      scope.type = null;
      scope.text = "";

      scope.$watch("value", function(newValue) {
        if (newValue < 2) {
          scope.type = "danger";
          scope.text = "Weak";
        } else if (newValue < 3) {
          scope.type = "warning";
          scope.text = "Acceptable";
        } else {
          scope.type = "primary";
          scope.text = "Strong";
        }
      });
    }
  };
}).
directive("singleErrorUpload", function() {
  return {
    restrict: "A",
    controller: ["$scope", function($scope) {
       $scope.$watch("file_error_msgs.length", function() {
          // Reset the error display flag when a new error is pushed
          $scope.displayErr = true;
       });

       $scope.displayErr = true;
    }],
    templateUrl: "views/partials/upload_error_msg.html",
  };
}).
directive("errorsUpload", function() {
  // Depends on file_error_msgs is defined in parent scope.
  return {
    restrict: "A",
    templateUrl: "views/partials/upload_error_msgs.html",
  };
}).
directive("extendFlowValidSize", ["uploadUtils", function(uploadUtils) {
  return {
    restrict: "A",
    scope: true,
    link: function(scope, iElment, iAttrs) {
      var validSize = parseInt(scope.$eval(iAttrs.extendFlowValidSize), 10);
      scope.$on("flow::fileAdded", function(event, _, flowFile) {
        if (flowFile.size > validSize) {
          if (typeof scope.file_error_msgs === "undefined") {
            scope.file_error_msgs = [];
          }
          var errMsg = uploadUtils.translateInvalidSizeErr(flowFile.name, validSize);
          scope.file_error_msgs.push(errMsg);
          event.preventDefault();
        }
      });
    }
  };
}]).
directive("imageUpload", function () {
  return {
    restrict: "A",
    scope: {
      imageUploadModel: "=",
      imageUploadModelAttr: "@",
      imageUploadId: "@",
      imageSrcUrl: "@"
    },
    templateUrl: "views/partials/image_upload.html",
    controller: "ImageUploadCtrl"
  };
}).
// pgpPubkeyValidator binds to text-areas to provide input validation on user
// input PGP public keys. Note that the directive attaches itself to the
// containing form's ngModelController NOT the ngModel bound to the value of the
// text-area itself. If the key word 'canBeEmpty' the pgp key validator is disabled
// when the textarea's input is empty.
directive("pgpPubkeyValidator", function() {
  // scope is the directives scope
  // elem is a jqlite reference to the bound element
  // attrs is the list of directives on the element
  // ngModel is the model controller attached to the form
  function link(scope, elem, attrs, ngModel) {
    scope.canBeEmpty = scope.pgpPubkeyValidator === "canBeEmpty";

    // modelValue is the models value, viewVal is displayed on the page.
    ngModel.$validators.pgpPubKeyValidator = function(modelVal) {
    // Check for obvious problems.
      if (typeof modelVal !== "string") {
        modelVal = "";
      }

      modelVal = modelVal.trim();

      if (scope.canBeEmpty && modelVal === "") {
        return true;
      }

      return modelVal.startsWith("-----BEGIN PGP PUBLIC KEY BLOCK-----") && modelVal.endsWith("-----END PGP PUBLIC KEY BLOCK-----");
    };
  }
  // Return a Directive Definition Object for angular to compile
  return {
    restrict: "A",
    require: "ngModel",
    link: link,
    scope: {
      // The string passed to the directive is used to assign special key word behavior.
      pgpPubkeyValidator: "@"
    }
  };
}).
directive("singleClick", [function() {
  return {
    restrict: "A",
    link: function(scope, elm) {
      elm.on("click", function() {
        elm.attr("disabled", true);
      });
    }
  };
}]).
directive("wbfile", [function() {
  return {
    restrict: "A",
    scope: false,
    templateUrl: "views/partials/wbfile.html"
  };
}]).
directive("fileInput", function() {
  return {
    restrict: "A",
    templateUrl: "views/partials/file_input.html",
    scope: {
      fileInput: "&",
      fileInputLabel: "@"
    },
    link: function (scope, iElement) {
      iElement.find("input").on("change", function (event) {
        if(event.target.files && event.target.files.length) {
          scope.$apply(function(){
            scope.fileInput({file: event.target.files[0]});
          });
        }
      });
    }
  };
}).
directive("isolateClick", function() {
  return {
    link: function(scope, elem) {
      elem.on("click", function(e){
        e.stopPropagation();
      });
    }
 };
}).
directive("disableCcp", function(){
  return {
    scope: {},
    link:function(scope,element) {
      element.on("cut copy paste", function (event) {
        event.preventDefault();
      });
    }
  };
}).
directive("convertToNumber", function() {
  return {
    require: "ngModel",
    link: function(scope, element, attrs, ngModel) {
      ngModel.$parsers.push(function(val) {
        return val !== null ? parseInt(val, 10) : null;
      });
      ngModel.$formatters.push(function(val) {
        return val !== null ? "" + val : null;
      });
    }
  };
}).
directive("passwordStrengthValidator", function() {
  function link(scope, elem, attrs, ngModel) {
    ngModel.$validators.passwordStrengthValidator = function(pwd) {
      var types = {
        lower: /[a-z]/.test(pwd),
        upper: /[A-Z]/.test(pwd),
        symbols: /\W/.test(pwd),
        digits: /\d/.test(pwd)
      };

      var i,
          variation1 = 0,
          variation2 = 0,
          letters = {},
          score = 0;

      if (pwd) {
        /* Score symbols variation */
        for (i in types) {
          variation1 += types[i] ? 1 : 0;
        }

        /* Score unique symbols */
        for (i = 0; i < pwd.length; i++) {
          if (!letters[pwd[i]]) {
            letters[pwd[i]] = 1;
            variation2 += 1;
          }
        }

        if (variation1 !== 4 || variation2 < 8 || pwd.length < 10) {
          score = 1;
        } else if (variation1 !== 4 || variation2 < 10 || pwd.length < 12) {
          score = 2;
        } else {
          score = 3;
        }
      }

      scope.$parent.passwordStrengthScore = score;

      return score > 1;
    };
  }

  return {
    restrict: "A",
    require: "ngModel",
    link: link,
    scope: {
      passwordStrengthValidator: "@"
    }
  };
});
