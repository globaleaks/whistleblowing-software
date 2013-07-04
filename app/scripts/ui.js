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
          img_receiver = element.parent().parent().find('img.baseimage'),
          headers = {'X-Session': $cookies['session_id']};

        img_receiver.hover(function(){
          // Resize the overlay black image to match the icon size.
          var upload_file = element.parent().parent().find('.uploadfile');
          upload_file.css('width', img_receiver[0].width + 10);
          upload_file.css('height', img_receiver[0].height - 20);
        });

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
                                                      headers: headers,
                                                      multipart: false}),
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
  directive('fileUpload', ['$rootScope', '$cookies', 'Node',
            function($rootScope, $cookies, Node){

    // The purpose of this directive is to register the jquery-fileupload
    // plugin

    return {

      templateUrl: 'views/widgets/fileupload.html',

      scope: {
        // Pass the action from the action attribute
        action: '@',
        // This tells to create a two way data binding with what is passed
        // inside of the element attributes (ex. file-upload="someModel")
        fileUploader: '=',
        maximumFilesize: '='
      },

      link: function(scope, element, attrs) {
        var headers = {'X-Session': $cookies['session_id']};

        function add(e, data) {
          for (var file in data.files) {
            var fileInfo,
              fileID;

            if (data.files[file].size >= (scope.maximumFilesize * 1024 * 1024) ) {
              var error = {};

              error.message = data.files[file].name +
                  " is too big. (Maximum filesize: " +
                  (scope.maximumFilesize / (1024*1024)) + " MB)";
              error.code = 39;

              if (!$rootScope.errors) {
                $rootScope.errors = [];
              }
              $rootScope.errors.push(error);
              data.files.splice(file, 1);
              scope.$apply();
              continue;
            };

            fileID = $rootScope.fileUploader.uploadedFiles.length + file;
            fileInfo = {'name': data.files[file].name,
              'filesize': data.files[file].size,
              'error': 'None',
              'type': data.files[file].type,
              'last_modified_date': data.files[file].lastModifiedDate,
              'file_id': fileID
            };

            var jqXHR = data.submit();
            fileInfo.abort = function() {
              jqXHR.abort();
            }
            $rootScope.fileUploader.uploadingFiles.push(fileInfo);
            scope.$apply();
          }
        };

        function progressMeter(e, data) {
          var progress_percent = parseInt(data.loaded / data.total * 100, 10);
          $(element[0]).find('.progress .bar').css('width', progress_percent + '%');
        };

        function done(e, data) {
          var fileInfo = data.result[0],
            textStatus = data.textStatus;

          $rootScope.fileUploader.uploadedFiles.push(fileInfo);
          $rootScope.fileUploader.uploadingFiles.pop(fileInfo);
          scope.$apply();
        };

        $(element[0]).fileupload({
          headers: headers,
          progress: progressMeter,
          progressall: progressMeter,
          multipart: false,
          add: add,
          done: done,
        });

        $rootScope.fileUploader.cancelAll = function() {
          $.each($rootScope.fileUploader.uploadingFiles, function(idx, fileInfo) {
            console.log(fileInfo);
            fileInfo.abort();
          });

          $(element[0]).find('.progress .bar').css('width', 0 + '%');
          $rootScope.fileUploader.uploadingFiles = [];
        }

      }
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
  directive('spinner', function(){
    return function(scope, element, attrs) {
      var opts = {
        lines: 17, // The number of lines to draw
        length: 31, // The length of each line
        width: 13, // The line thickness
        radius: 50, // The radius of the inner circle
        corners: 1, // Corner roundness (0..1)
        rotate: 0, // The rotation offset
        direction: 1, // 1: clockwise, -1: counterclockwise
        color: '#000', // #rgb or #rrggbb
        speed: 1, // Rounds per second
        trail: 38, // Afterglow percentage
        shadow: false, // Whether to render a shadow
        hwaccel: false, // Whether to use hardware acceleration
        className: 'spinner', // The CSS class to assign to the spinner
        zIndex: 2e9, // The z-index (defaults to 2000000000)
        top: 'auto', // Top position relative to parent in px
        left: 'auto' // Left position relative to parent in px
      }, spinner = new Spinner(opts).spin(element[0]);
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
