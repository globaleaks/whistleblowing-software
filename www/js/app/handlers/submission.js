/*global window */

define(function (require) {
    'use strict';

    var $ = require('jquery'),
        hogan = require('hogan'),
        template = hogan.compile(require('text!../templates/submission.html'));

    require('jquery.file.upload');

    function fileUpload(element) {
      element.fileupload();

      element.fileupload(
        'option',
        'redirect',
        window.location.href.replace(
            /\/[^\/]*$/,
            '/cors/result.html?%s'
        )
      );

      if (window.location.hostname === 'blueimp.github.com') {
        // Demo settings:
        element.fileupload('option', {
          url: '//jquery-file-upload.appspot.com/',
          maxFileSize: 5000000,
          acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i,
          process: [
            {
              action: 'load',
              fileTypes: /^image\/(gif|jpeg|png)$/,
              maxFileSize: 20000000 // 20MB
            },
            {
              action: 'resize',
              maxWidth: 1440,
              maxHeight: 900
            },
            {
              action: 'save'
            }
            ]
        });
        // Upload server status check for browsers with CORS support:
        if ($.support.cors) {
          $.ajax({
            url: '//jquery-file-upload.appspot.com/',
            type: 'HEAD'
          }).fail(function () {
            $('<span class="alert alert-error"/>')
                .text('Upload server currently unavailable - ' +
                        new Date())
                .appendTo('#fileupload');
          });
        }
      } else {
        // Load existing files:
        element.each(function () {
          var that = this;
          $.getJSON(this.action, function (result) {
            if (result && result.length) {
              $(that).fileupload('option', 'done')
                  .call(that, null, {result: result});
            }
          });
        });
      }
    };
    return function submissionHandler(data) {
      var content = template.render(data);
      $('.contentElement').html(content);
      require('../uiSubmission')();

    };
});
