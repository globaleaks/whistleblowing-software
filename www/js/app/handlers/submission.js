/*global window */

define(function (require) {
  'use strict';

  var $ = require('jquery'),
      hogan = require('hogan'),
      templates = {},
      requests = {},
      nodeinfo = {},
      ui = {};

  ui.submission = require('../ui/ui.submission');

  templates.submission = hogan.compile(require('text!../templates/submission.html'));
  templates.fileupload = hogan.compile(require('text!../templates/fileupload.html'));
  templates.filelist = hogan.compile(require('text!../templates/filelist.html'));

  requests.node = require('../requests/node');
  requests.submission = require('../requests/submission');


  function fileUpload(element) {
    //console.log("running on ");
    //console.log(element);
    // Iframe transport for file upload
    require('jquery.iframe-transport');
    // Load jquery file uploader
    require('jquery.fileupload');

    // XXX decided not to go for using this. Investigate if there is some stuff in
    // it that we would like to take.
    // Load file processing plugin
    //require('jquery.fileupload-fp');
    //
    // XXX This is possibly more generic and could work well for us. Try it out!
    //require('jquery.fileupload-ui');

    element.fileupload({
      progress: function (e, data) {
        console.log(data);
        var progress = parseInt(data.loaded / data.total * 100, 10);
        $('#progress .bar').css(
              'width', progress + '%'
        );
      },
      progressall: function (e, data) {
          var progress = parseInt(data.loaded / data.total * 100, 10);
          $('#progress .bar').css(
              'width',
              progress + '%'
          );
      },
      add: function (e, data) {
          //console.log("ADDING");
          //console.log(data);
          var filelist =  "";

          for (var file in data.files) {

            var file_info,
                item_id = data.files[file].name.replace(/\./g, "");

            file_info = {'name': data.files[file].name,
              'filesize': data.files[file].size,
              'error': 'None',
              'type': data.files[file].type,
              'last_modified_data': data.files[file].lastModifiedDate,
              'item_id': item_id
                };

            filelist += templates.filelist.render(file_info);
          }
          //console.log("Rendered");
          //console.log(filelist);
          $('.files').append(filelist);

          data.submit();
          //data.context = $('<p/>').text('Uploading...').appendTo(element);
      },
      done: function (e, data) {
          var result = data.result,
              textStatus = data.textStatus,
              item_id;
          //console.log("Finished!");
          //console.log(result);
          //
          // XXX do sanitization and validation here
          result = JSON.parse(result);
          // XXX this is a hack to keep track of what things are finished.
          // fix this by having a lookup table of the in progress submissions
          // and their element id.
          item_id = result[0].name.replace(/\./g, "");
          $("#"+item_id+" .bar").css('width', "100%");
      }
    });


  }

  return function submissionHandler(data) {
    var submission = templates.submission.render(data);
    $('.contentElement').html(submission);

    requests.node.root().done(function(data) {
      var contexts;
      nodeinfo = data;
      nodeinfo.contexts = ui.submission.processContexts(nodeinfo.contexts);
      nodeinfo.context_selected = nodeinfo.contexts[0].id;
      requests.submission.root().done(function(submission) {
        ui.submission.processForm(nodeinfo.contexts[0].fields, nodeinfo, submission);
        var fileupload = templates.fileupload.render({submission_id:
                                    submission['submission_id']});
        $('.fileUpload').html(fileupload);
        fileUpload($("#fileupload"));
        //debugDeck();
      });
    });
  };
});
