// In here shall go all UI related modules that contain directives
// Directives are a way of manipulating the DOM or how the angular developers
// put it, "it's a way to teach HTML some new tricks".
//
// Basically by registering a directive you are then able to set the attribute
// of a tag to a directive defined here and then you will be able to interact
// with it.
// To learn more see: http://docs.angularjs.org/guide/directive
angular.module('submissionUI', [], function($compileProvider) {
  $compileProvider.directive('submissionField', function($compile){
    // We are now able to do something like <div submission-field=""></div> and
    // then stuff will happen to that field. This is required to have our
    // dynamic generation of HTML elements.
    return function(scope, element, attrs) {
      var fieldtype = scope.field.type,
        placeholder = scope.field.value,
        required = scope.field.required,
        // this is the basic template for dynamic creation of the submission
        // form that are of input type
        // XXX refactor these to use the templating system of angular
        input_template = '<input type="<%= type %>"'+
                ' placeholder="<%= placeholder %>"' +
                ' required="<%= required %>">',
        // This is the basic template for dynamic creation of submission form
        // that is of textarea type
        textarea_template = '<textarea placeholder="<%= placeholder %>"'+
                ' required="<%= required %>"></textarea>';

      console.log("This field has type " + fieldtype);
      // XXX perhaps we can change the API to better accomodate this
      if ( fieldtype == "text" ) {
        $(element).replaceWith(_.template(textarea_template, {
          'placeholder': placeholder, 'required': required}));
      } else if ( fieldtype == "string" )  {
        $(element).replaceWith(_.template(input_template, {'type': 'text',
          'placeholder': placeholder, 'required': required}));
      } else if ( fieldtype == "radio" ){
        // XXX add support for radio buttons.
      } else if ( fieldtype == "other type" ) {
        // XXX and something else...
      }
    }
  });

  // XXX this needs some major refactoring.
  $compileProvider.directive('fileUpload', function($compile){
    // The purpose of this directive is to register the jquery-fileupload plugin
    return function(scope, element, attrs) {
      $(element).fileupload({
        progress: function (e, data) {
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
  });
});
