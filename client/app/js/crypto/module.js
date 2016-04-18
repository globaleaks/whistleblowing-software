angular.module('GLBrowserCrypto', [])

// pgpPubKeyDisplay displays the important details from a public key.
.directive('pgpPubkeyDisplay', function() {
  
  // Create object that displays relevant key details to the user. This function
  // returns fingerprint, key id, creation date, and expiration date. If the parse
  // fails the function returns undefined.
  function pgpKeyDetails(armoredText) {
    // Catch the obivous errors and save time!
    if (typeof armoredText !== 'string' || !armoredText.startsWith('---')) {
      return;
    }
    var res = openpgp.key.readArmored(armoredText);

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
    restrict: 'E',
    templateUrl: '/views/partials/pgp/pubkey_display.html',
    scope: {
      keyStr: '=keyStr',

    },
    controller: ['$scope', function($scope) {
      $scope.$watch('keyStr', function(newVal, oldVal) {
        if (newVal === "") {
          return;
        }
        $scope.key_details = pgpKeyDetails(newVal);
      });
  }]};
})

// pgpPubkeyInput is an element directive that can display validated pgp
// public keys. The attached-model attribute will be bound to the input of the
// text area.
.directive('pgpPubkeyInput', function() {

  return {
    restrict: 'E',
    templateUrl: '/views/partials/pgp/pubkey_input.html',
    scope: {
      localModel: '=attachedModel',
      keyForm: '=attachedForm',
    },
    controller: ['$scope', function($scope) {
      
      // The key point of the controller occurs when the keyForm._pubKeyInp input 
      // becomes valid. When that happens the public key attached via localModel
      // is now both ready for use elsewhere in the application and for display
      $scope.$watch('keyForm._pubKeyInp.$valid', function(newVal, oldVal) {
        // When the watch is init this case fires.
        if (oldVal === newVal) {
          return;
        }

        // The PGP Key is valid. Extract its details.
        if (newVal) {
          $scope.keyStr = $scope.keyForm._pubKeyInp.$modelValue;
        } else {
          // If the key has changed due to new input, dereference old key_details.
          $scope.keyStr = undefined;
        }
      });
    }],
  };
})

// pgpPubkeyValidator binds to text-areas to provide input validation on user
// input GPG public keys. Note that the directive attaches itself to the 
// containing form's ngModelController NOT the ngModel bound to the value of the 
// text-area itself.
.directive('pgpPubkeyValidator', function() {
  
  // Checks to see if passed text is an ascii armored GPG public key.
  function validatePubKey(textInput) {
    // Check for obvious problems.
    if (typeof textInput !== 'string') {
      return false; 
    }
    var s = textInput.trim();
    if (!s.startsWith('-----')) {
      return false;
    }

    // Try to parse the key.
    var result;
    try {
      result = openpgp.key.readArmored(s);
    } catch (err) {
      console.log(err);
      return false;
    }
    
    // Assert that the parse created no errors.
    if (angular.isDefined(result.err)) {
      return false;
    }

    // Assert that there is only one key in the input.
    if (result.keys.length !== 1) {
      return false;
    }
    
    var key = result.keys[0];
    // Assert that the key type is not private and the public flag is set.
    if (key.isPrivate() || !key.isPublic()) {
      // Woops, the user just pasted a private key
      delete key;
      delete result;
      return false;
    }
    
    return true;
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
