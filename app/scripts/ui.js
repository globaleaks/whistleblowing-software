// In here shall go all UI related modules that contain directives
// Directives are a way of manipulating the DOM or how the angular developers
// put it, "it's a way to teach HTML some new tricks".
//
// Basically by registering a directive you are then able to set the attribute
// of a tag to a directive defined here and then you will be able to interact
// with it.
// To learn more see: http://docs.angularjs.org/guide/directive
angular.module('submissionUI', []).
  directive('pragmaticFileUpload', ['$cookies', function($cookies){

    return {

      link: function(scope, element, attrs) {
        var selectFileButton = element.find('button.selectFile'),
          uploadButton = element.find('button.upload'),
          img_receiver = element.parent().parent().find('img.baseimage')[0],
          headers = {'X-Session': $cookies['session_id']};

        img_receiver.onload = function(){
          // Resize the overlay black image to match the icon size.
          var upload_file = element.parent().parent().find('.uploadfile');
          upload_file.css('width', img_receiver.width + 10);
          upload_file.css('height', img_receiver.width - 20);
        };

        $(element).find('input[type="file"]').change(function(){
          scope.changeProfile();
        });

        scope.$watch(attrs.src, function(){
          var url = attrs.src;

          if (url[0] === "'")
            url = url.replace(/'/g, "");

          $(uploadButton).click(function() {
            console.log("uploading to " + url);
            var fileUploader = $(element).fileupload({url: url,
                                                      headers: headers}),
              filesList = element.find('input.file')[0].files;

            $(element).fileupload('send', {files: filesList}).
              success(function(result, textStatus, jqXHR) {
                console.log("Successfully uploaded");
                  original_src = img_receiver.src;

                img_receiver.src = original_src+'?'+ Math.random();
                element.parent().hide();
            }).
              error(function(jqXHR, textStatus, error) {
                console.log("There was a problem");
            }).
              complete(function(result, textStatus, jqXHR) {
                console.log("All complete");
            });

          });

        });
      }
    }
}]).
  // XXX this needs some major refactoring.
  directive('fileUpload', ['$rootScope', '$cookies', function($rootScope, $cookies){

    // The purpose of this directive is to register the jquery-fileupload
    // plugin

    return {

      templateUrl: 'views/widgets/fileupload.html',

      scope: {
        // Pass the action from the action attribute
        action: '@',
        // This tells to create a two way data binding with what is passed
        // inside of the element attributes (ex. file-upload="someModel")
        uploadedFiles: '=',
        uploadingFiles: '='
      },

      link: function(scope, element, attrs) {
        var headers = {'X-Session': $cookies['session_id']};

        function add(e, data) {
          for (var file in data.files) {
            var file_info,
              file_id = $rootScope.uploadedFiles.length + file;

            file_info = {'name': data.files[file].name,
              'filesize': data.files[file].size,
              'error': 'None',
              'type': data.files[file].type,
              'last_modified_date': data.files[file].lastModifiedDate,
              'file_id': file_id
            };

            $rootScope.uploadingFiles.push(file_info);
            scope.$apply();
          }
          data.submit();
        };

        function progressMeter(e, data) {
          var progress_percent = parseInt(data.loaded / data.total * 100, 10);
          $(element[0]).find('.progress .bar').css('width', progress_percent + '%');
        };

        function done(e, data) {
          var file_info = data.result[0],
            textStatus = data.textStatus,
            item_id;

          $rootScope.uploadedFiles.push(file_info);
          $rootScope.uploadingFiles.pop(file_info);
          scope.$apply();
        };

        $(element[0]).fileupload({progress: progressMeter,
          progressall: progressMeter, add: add, done: done,
          headers: headers});
      }
    }
}]).
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

}]).
  directive('bsPopover', function(){
      return function(scope, element, attrs) {
        // We watch to see when the bsPopover attribute is sets
        scope.$watch(attrs.bsPopover, function(value){
          if (attrs.bsPopover) {
            element.popover({'title': attrs.bsPopover});
          }
        });
      };
}).
  directive('holder', function(){
      return function(scope, element, attrs) {
        var size = attrs.holder;
        Holder.run();
      };
}).
  directive('fadeout', function(){
    return function(scope, element, attrs) {
      element.fadeOut(3000);
    };
}).
  directive('expandTo', function() {
  // Used to expand the element to the target width when you over over it. Also
  // makes sure that all the text is selected on a single click.
  return function(scope, element, attrs) {
    scope.$watch(attrs.expandTo, function(width){
      var original_width = element.css('width'),
        target_width = width + 'px';

      element.mouseenter(function() {
        element.css('width', target_width);
      });

      element.mouseleave(function() {
        element.css('width', original_width);
      });

      element.click(function() {
        element.select();
      });

    })
  };
});
