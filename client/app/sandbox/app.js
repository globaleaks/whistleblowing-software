angular.module('GLClient', [])
.controller('MainCtrl', ['$scope', function($scope) {
  rec = { 
    pgp_key_public: "",
    email: "nskelsey@gmail.com",
  }; 
  $scope.receiver = rec;
}])
// pgppubkeyinput is an element directive that can display and validate pgp
// public keys. The attached-model attribute will be bound to the input of the
// text area.
.directive('pgppubkeyinput', function() {
  
  // Craete object from valid pubKey
  function pgpKeyDetails(pubKey) {
    // TODO
  }

  return {
    restrict: 'E',
    templateUrl: '/sandbox/pub_key_input.html',
    scope: {
      localModel: '=attachedModel',
    },
    controller: ['$scope', function($scope) {
      // The key point of the controller occurs when the keyForm.txt input 
      // becomes valid. When that happens the public key attached via localModel
      // is now both ready for use elsewhere in the application and for display
      $scope.$watch('keyForm.txt.$valid', function(newVal, oldVal) {
        console.log("into digest", newVal, oldVal);
        // When the watch is init this case fires.
        if (oldVal === newVal) {
          return;
        }

        // The GPGKey is valid. Extract its details.
        if (newVal) {
          $scope.key_details = {
            'username': 'e@e.com',
            'name': 'John Doe',
            'expires': '10-10-2020',
          };      
          // TODO extract key details
        } else {
          // If the key has changed due to new input, dereference old key_details.
          $scope.key_details = undefined;
        }
      });
    }],
  };
})

// pgpPubKeyValidator binds to text-areas to provide input validation on user
// input GPG public keys. Note that the directive attaches itself to the 
// containing form's ngModelController NOT the ngModel bound to the value of the 
// text-area itself.
.directive('pgpPubKeyValidator', function() {
  // Checks to see if passed text is an ascii armored GPG public key.
  function validatePubKey(textInput) {
    // TODO
    if (textInput === 'b' || textInput === 'c') {
      return true;
    }
    return false;
  }
  
  // scope is the directives scope
  // elem is a jqlite reference to the bound element
  // attrs is the list of directives on the element
  // ngModel is the model controller attached to the form
  function link(scope, elem, attrs, ngModel){
    // modelValue is the models value, viewVal is displayed on the page.
    ngModel.$validators.pgpPubKeyValidator = function(modelVal, viewVal) {
      return validatePubKey(modelVal);
    };
  }
  // Return a Directive Definition Object for angular to compile
  return {
    require: 'ngModel',
    link: link,
  };
});
