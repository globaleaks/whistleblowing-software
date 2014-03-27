// In here shall go all UI related modules that contain directives
// Directives are a way of manipulating the DOM or how the angular developers
// put it, "it's a way to teach HTML some new tricks".
//
// Basically by registering a directive you are then able to set the attribute
// of a tag to a directive defined here and then you will be able to interact
// with it.
// To learn more see: http://docs.angularjs.org/guide/directive
angular.module('submissionUI', []).
  directive('genericFileUpload', [ '$route', 'Authentication', function($route, Authentication){

    return {

      link: function(scope, element, attrs) {
        var selectFileButton = element.find('button.selectFile');
        var uploadButton = element.find('button.upload');

        function progressMeter(e, data) {
          var progress_percent = parseInt(data.loaded / data.total * 100, 10);
          $(element).parent().find('.uploadProgress .progress .bar').css('width', progress_percent + '%');
        };

        $(element).find('input[type="file"]').change(function(){
          scope.markFileSelected();
        });

        scope.$watch(attrs.src, function(){
          var url = attrs.src,
            fileUploader = $(element).fileupload({
              url: url,
              headers: Authentication.headers(),
              multipart: false,
              progress: progressMeter,
              progressall: progressMeter,
              add: function(e, data){
                $(element).parent().find('.uploadProgress').show();
                var filesList = $(element).find('input[type="file"]')[0].files,
                  jqXHR = data.submit({files: filesList});

                jqXHR.success(function(result, textStatus, jqXHR) {
		                scope.uploadfinished();
                    $(element).parent().find('.uploadProgress').hide();
                });
              }
            });

        });
      }
    }
}]).

  directive('pragmaticFileUpload', [ '$route', 'Authentication', function($route, Authentication){

    return {

      link: function(scope, element, attrs) {
        var selectFileButton = element.find('button.selectFile');
        var uploadButton = element.find('button.upload');
        var img = element.parent().parent().find('img.baseimage')[0];

        function progressMeter(e, data) {
          var progress_percent = parseInt(data.loaded / data.total * 100, 10);
          $(element).parent().find('.uploadProgress .progress .bar').css('width', progress_percent + '%');
        };

        $(element).find('input[type="file"]').change(function(){
          scope.markFileSelected();
        });

        scope.$watch(attrs.src, function(){
          var url = attrs.src,
            fileUploader = $(element).fileupload({
              url: url,
              headers: Authentication.headers(),
              multipart: false,
              progress: progressMeter,
              progressall: progressMeter,
              add: function(e, data){
                $(element).parent().find('.uploadProgress').show();
                var filesList = $(element).find('input[type="file"]')[0].files,
                  jqXHR = data.submit({files: filesList});

                jqXHR.success(function(result, textStatus, jqXHR) {

                    if (img !== undefined) {
                        img.src += '?'+ Math.random();
                    }

                    $(element).parent().find('.uploadProgress').hide();
                });
              }
            });

        });
      }
    }
}]).
  directive('spinner', function(){
    return function(scope, element, attrs) {
      var opts = {
        lines: 13, // The number of lines to draw
        length: 20, // The length of each line
        width: 10, // The line thickness
        radius: 30, // The radius of the inner circle
        corners: 1, // Corner roundness (0..1)
        rotate: 0, // The rotation offset
        direction: 1, // 1: clockwise, -1: counterclockwise
        color: '#000', // #rgb or #rrggbb or array of colors
        speed: 1, // Rounds per second
        trail: 60, // Afterglow percentage
        shadow: false, // Whether to render a shadow
        hwaccel: false, // Whether to use hardware acceleration
        className: 'spinner', // The CSS class to assign to the spinner
        zIndex: 2e9, // The z-index (defaults to 2000000000)
        top: '50%', // Top position relative to parent in px
        left: '50%' // Left position relative to parent in px
      }, spinner = new Spinner(opts).spin(element[0]);
  };
}).
  directive('fadeout', function(){
    return function(scope, element, attrs) {
      var fadeout_delay = 3000;

      element.mouseenter(function(){
        element.stop().animate({opacity:'100'});
      });
      element.mouseleave(function(){
        element.fadeOut(fadeout_delay);
      });

      element.fadeOut(fadeout_delay);
    };
}).
  directive('glClock', function() {
    return function(scope, element, attrs) {
      var clock = $(element).FlipClock({});
      clock.setTime(scope.seconds);
      clock.setCountdown(true);
    }
});

