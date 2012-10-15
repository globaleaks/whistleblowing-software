/*global window */

define(function (require) {
  'use strict';

  var $ = require('jquery'),
      hogan = require('hogan'),
      templates = {},
      requests = {},
      nodeinfo = {},
      ui = {};

  templates.submission = hogan.compile(require('text!../templates/submission.html'));
  templates.fileupload = hogan.compile(require('text!../templates/fileupload.html'));
  templates.filelist = hogan.compile(require('text!../templates/filelist.html'));
  templates.receipt = hogan.compile(require('text!../templates/receipt.html'));

  requests.node = require('../requests/node');
  requests.submission = require('../requests/submission');


  function fileUpload(element) {
    console.log("running on ");
    console.log(element);
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

  function renderTemplate(template, data) {
      if (data.help) {
          template += '<span class="help-block">{{help}}</span>'
      }
      var cTemplate = hogan.compile(template);
      var rendered = cTemplate.render(data);
      // console.log(rendered);
      return rendered;
  };

  var  process = {
      string: function(data) {
          var template;
          template = '<label>{{label}}</label>\n';

          template += '<input type="text" name="{{name}}"';
          template +=        'value="{{default}}" placeholder="{{hint}}"';
          template +=        'required="{{required}}"/>';

          return renderTemplate(template, data);
      },

      text: function(data) {
          var template;
          template = '<label>{{label}}</label>\n';
          template += '<textarea name="{{name}}" required={{required}}>{{default}}</textarea>\n';
          return renderTemplate(template, data);
      },

      checkbox: function(data) {
          var template;
          template = '<label class="checkbox">\n';
          template += '<input type="checkbox" name="{{name}}" required={{required}}>{{label}}\n';
          template += '</label>';
          return renderTemplate(template, data);
      },

      radio: function(data) {
          var x,
              template = '',
              parsed_data = data;

          for (x in data.options) {
              parsed_data['label'+x] = data.options[x].label;
              parsed_data['value'+x] = data.options[x].value;
              template += '<label class="radio">\n';
              template += '<input type="radio" name="{{name}}" value="{{value'+x+'}}" required={{required}}>\n';
              template += '{{label'+x+'}}\n';
              template += '</label>';
          }
          return renderTemplate(template, parsed_data);
      }
  };

  function processFields(form) {
      var form_spec = form.serializeArray(),
          fields = {};
      for (var field in form_spec) {
        fields[form_spec[field].name] = form_spec[field].value;
      }
      return fields;
  };

  function showReceipt(receipt_id) {
      $('.submission').html(templates.receipt.render({'receipt_id': receipt_id}));
  };

  function generateForm(form) {
      var formContent = {left: [], right: []}
      var x, target,
          allowed_types = ['string', 'text','checkbox', 'radio'];
      for (x in form) {
        if (allowed_types.indexOf(form[x].type) != -1) {
          var element, position;
          if ((x % 2) == 0) {
            position = formContent.left;
          } else {
            position = formContent.right;
          }
          element = process[form[x].type](form[x]);
          position.push(element);
        }
      };
      return formContent;
  };

  function getContextFields(nodeinfo) {
    for (var name in nodeinfo.contexts) {
      var context = nodeinfo.contexts[name];
      if (context.id == nodeinfo.context_selected) {
        return context.fields;
      }
    }
  };


  function processForm(fields, nodeinfo, submission) {
    var form_content = generateForm(fields);

    $('.submissionFormLeft')[0].innerHTML = "";
    $('.submissionFormRight')[0].innerHTML = "";
    //$('.submissionForm button').remove();
    //$('.submissionForm').remove();

    //console.log("Adding");
    //console.log(form_content);
    for (var el in form_content.left) {
      $('.submissionFormLeft').append(form_content.left[el]);
    }

    for (var el in form_content.right) {
      $('.submissionFormRight').append(form_content.right[el]);
    }
    // XXX still too much nesting, but it's probably phisiological
    $('.submissionForm').change(function() {

      if ($('.submissionForm').valid()) {
        $('button#submit_button').addClass('btn-success');
        $('button#submit_button').removeClass('disabled');
        $('button#submit_button').removeClass('btn-warning');

        $('button#submit_button').click(function(){
          var fields = processFields($('.submissionForm'));
          console.log("Going for the hit with " + nodeinfo.context_selected);
          requests.submission.status_post(submission['submission_id'],
                {'fields': fields,
                 'context_selected': nodeinfo.context_selected}).done(function(args){
            var proposed_receipt = "ididntchangeit",
            folder_name = "foldername",
            folder_description = "folderdesc";
            requests.submission.finalize_post(submission['submission_id'],
              proposed_receipt, folder_name,
              folder_description).done(function(data){
              showReceipt(data.receipt);
            });
          });
          return false;
        });
      } else {
        $('button#submit_button').addClass('btn-warning');
        $('button#submit_button').addClass('disabled');
        $('button#submit_button').removeClass('btn-success');
      }
      return false;
    });
  };


  function processContexts(nodeinfo) {
      var context_selector = $("#context_selector"),
          context_id, fields;

      context_selector.change(function(){
        context_id = $('#context_selector option:selected')[0].value;
        nodeinfo.context_selected = context_id;
        console.log(nodeinfo);
        fields = getContextFields(nodeinfo);
        console.log(fields);
        requests.submission.root().done(function(submission){
          processForm(fields, nodeinfo, submission);
        });
      });
      for (var i in nodeinfo.contexts) {
        // XXX do validation here.
        var context_option = "<option value=" + nodeinfo.contexts[i].id + ">";

        context_option += nodeinfo.contexts[i].name + "</option>";
        context_selector.append(context_option);
      };
      return nodeinfo.contexts;
  };

  return function submissionHandler(data) {
    var submission = templates.submission.render(data);
    $('.contentElement').html(submission);

    requests.node.root().done(function(data) {
      var contexts;
      nodeinfo = data;
      nodeinfo.contexts = processContexts(nodeinfo);
      nodeinfo.context_selected = nodeinfo.contexts[0].id;
      requests.submission.root().done(function(submission) {
        processForm(nodeinfo.contexts[0].fields, nodeinfo, submission);

        var fileupload = templates.fileupload.render(submission);
        $('.fileUpload').html(fileupload);
        fileUpload($("#fileupload"));

        //debugDeck();
      });
    });
  };
});
