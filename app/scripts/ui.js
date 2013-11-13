// In here shall go all UI related modules that contain directives
// Directives are a way of manipulating the DOM or how the angular developers
// put it, "it's a way to teach HTML some new tricks".
//
// Basically by registering a directive you are then able to set the attribute
// of a tag to a directive defined here and then you will be able to interact
// with it.
// To learn more see: http://docs.angularjs.org/guide/directive
angular.module('submissionUI', []).
  directive('pragmaticFileUpload', [function(){

    return {

      link: function(scope, element, attrs) {
        var selectFileButton = element.find('button.selectFile'),
          uploadButton = element.find('button.upload'),
          img_receiver = element.parent().parent().find('img.baseimage'),
          headers = {'X-Session': $.cookie('session_id'),
                     'X-XSRF-TOKEN': $.cookie('XSRF-TOKEN')};

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
              headers: headers,
              multipart: false,
              progress: progressMeter,
              progressall: progressMeter,
              add: function(e, data){
                $(element).parent().find('.uploadProgress').show();
                var filesList = $(element).find('input[type="file"]')[0].files,
                  jqXHR = data.submit({files: filesList});
                
                jqXHR.success(function(result, textStatus, jqXHR) {
                    original_src = img_receiver[0].src;

                    img_receiver[0].src = original_src+'?'+ Math.random();

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
