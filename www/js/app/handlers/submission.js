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

  requests.node = require('../requests/node');
  requests.submission = require('../requests/submission');

  require('jquery.iframe-transport');
  require('jquery.fileupload');

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

  return function submissionHandler(data) {
    var submission = templates.submission.render(data);
    $('.contentElement').html(submission);
    requests.node.root().done(function(data) {
      var contexts;
      nodeinfo = data;
      nodeinfo.contexts = ui.submission.processContexts(nodeinfo.contexts);
      nodeinfo.context_selected = nodeinfo.contexts[0].id;
      ui.submission.processForm(nodeinfo.contexts[0].fields);
      requests.submission.root().done(function(submission) {
        var fileupload = templates.fileupload.render({submission_id:
                                    submission['submission_id']});
        $('.fileUpload').html(fileupload);
        fileUpload($("#fileupload"));
        //debugDeck();
      });
    });
  };
});
