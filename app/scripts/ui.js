// In here shall go all UI related modules that contain directives
// Directives are a way of manipulating the DOM or how the angular developers
// put it, "it's a way to teach HTML some new tricks".
//
// Basically by registering a directive you are then able to set the attribute
// of a tag to a directive defined here and then you will be able to interact
// with it.
// To learn more see: http://docs.angularjs.org/guide/directive
angular.module('submissionUI', []).
  // XXX this needs some major refactoring.
  directive('fileUpload', function(){
    // The purpose of this directive is to register the jquery-fileupload
    // plugin
    return function(scope, element, attrs) {
      $(element).fileupload({
        progress: function (e, data) {
          console.log("loaded file uploader!");
          var progress = parseInt(data.loaded / data.total * 100, 10);
          console.log($(element).find('.progress .bar'));
          $(element).find('.progress .bar').css(
                'width', progress + '%'
          );
          console.log("Progress " + progress);
        },

        progressall: function (e, data) {
          var progress = parseInt(data.loaded / data.total * 100, 10);
          $(element).find('.progress .bar').css(
                'width', progress + '%'
          );
          console.log("Progress " + progress);
        },

        add: function (e, data) {
          for (var file in data.files) {
            var file_info,
              file_id = scope.uploaded_files.length + file;

            file_info = {'name': data.files[file].name,
              'filesize': data.files[file].size,
              'error': 'None',
              'type': data.files[file].type,
              'last_modified_date': data.files[file].lastModifiedDate,
              'file_id': file_id
            };

            scope.$apply(function() {
              scope.uploaded_files.push(file_info);
            });

          }
          data.submit();
        },

        done: function (e, data) {
          var result = data.result,
            textStatus = data.textStatus,
            item_id;
          console.log(data);
          // XXX do sanitization and validation here
          // XXX this is a hack to keep track of what things are finished.
          // fix this by having a lookup table of the in progress submissions
          // and their element id.
          item_id = result[0].name.replace(/\./g, "");
          $("#"+item_id+" .bar").css('width', "100%");
        }
      });
    }
}).
  directive('latenzaBox', ['$timeout', function($timeout){
    return function(scope, element, attrs) {
      // This directive serves for making our latenza box work.
      //
      // Basically you are able to set the loading variable in
      // global scope to either true or false. When it is set
      // to true the loading box will be displayed and a
      // message containing some trivia on whistleblowing will
      // be displayed.
      //
      // Basically you must just do as follows:
      // $scope.loading = true (if loading is in progress)
      // $scope.loading = false (if loading has completed)
      //
      // XXX in future there may acutally be a cleaner way of
      // doing this.

      $timeout(function(){
        // XXX this is a hack to avoid calling the watch while
        // there is an apply in progress. Basically $timeout will
        // execute what is contained in the function when
        // everything that needs to happen in a digest cycle has
        // happened. This was the solution that people interested
        // in doing things like this have reached. See:
        // http://stackoverflow.com/questions/11135864/scope-watch-is-not-updating-value-fetched-from-resource-on-custom-directive
        // http://jsfiddle.net/jtowell/j8hnr/
        // https://github.com/angular/angular.js/issues/1250
        scope.$watch('loading', function() {
            if (scope.loading === true) {
              element.modal('show');
            } else if (scope.loading === false){
              element.modal('hide');
            } else {
              element.modal('show');
            }
          }, true);
      });

    }

}]);
