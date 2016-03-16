"use strict";

angular.module('GLDirectives', []).
  directive('fadeout', function(){
    return function(scope, element, attrs) {
      var fadeout_delay = 3000;

      element.mouseenter(function() {
        element.stop().animate({opacity:'100'});
      });
      element.mouseleave(function() {
        element.fadeOut(fadeout_delay);
      });

      element.fadeOut(fadeout_delay);
    };
}).
  directive('inputPrefix', [function() {
    return {
      require: 'ngModel',
      link: function(scope, elem, attrs, controller) {
        function inputPrefix(value) {
          var prefix = attrs.prefix;

          var result = prefix;

          if (value.length >= prefix.length) {
            if (value.slice(0, prefix.length) != prefix) {
              result = prefix + value;
            } else {
              result = value;
            }
          }

          controller.$setViewValue(result);
          controller.$render();

          return result;
        }

        controller.$formatters.push(inputPrefix);
        controller.$parsers.push(inputPrefix);
      }
    };
}]).
  directive('keycodevalidator', [function() {
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
}]).
 directive("fileread", [function () {
   return {
     scope: {
       fileread: "="
     },
     link: function (scope, element, attributes) {
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
}]);
