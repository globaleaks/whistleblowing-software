define(function (require) {
  'use strict';

  var $ = require('jquery'),
      network = require('network'),
      latenza = require('latenza'),
      hogan = require('hogan'),
      templates = {},
      requests = {},
      nodeinfo = {};

  templates.receipt = hogan.compile(require('text!../templates/receipt.html'));
  requests.submission = require('../requests/submission');
  requests.node = require('../requests/node');

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
      $('.submissionForm').hide();
      $('.receipt').show();
      $('.receipt').html(templates.receipt.render({'receipt_id': receipt_id}));
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



  return {
    debugDeck: function() {
      var debug = require('../debug'),
          dummy_requests = require('../dummy/requests'),
          submissionID = null;

      $("#node_button").click(function() {
        latenza.ajax({'url': '/node',
                      'type': 'GET'
        }).done(function(data) {
          debug.write(data, 'GET /node');
        });
      });

      $("#create_new").click(function() {
        requests.submission.root().done(function(data) {
                submissionID = data['submission_id'];
                debug.write(data, 'GET /submission');
        });
      });

      $("#send_fields").click(function() {
        if (submissionID) {
          var fields = {"FieldA": "hello", "FieldB": "world!"};
          var path = '/submission/'+submissionID+'/status';
          requests.submission.status_post(submissionID, {'fields': fields}).done(function(data){
            debug.write(data, 'POST '+path);
          });

        } else {
          alert("Run create new first!");
        }
      });

      $("#select_context").click(function() {
        if (submissionID) {
          var path = '/submission/'+submissionID+'/status';
          requests.submission.status_post(submissionID, {'context_selected':
                          nodeinfo.context_selected}).done(function(data){
            debug.write(data, 'POST '+path);
          });

        } else {
          alert("Run create new first!");
        }
      });

      $("#status").click(function() {
        var request = dummy_requests.submissionStatusPost;
        if (submissionID) {
          var path = '/submission/'+submissionID+'/status';
          requests.submission.status_get(submissionID).done(function(data){
            debug.write(data, 'GET '+path);
          });

        } else {
          alert("Run create new first!");
        }
      });

      $("#finalize_button").click(function() {
        if (submissionID) {
          var request = {'proposed_receipt': 'igotnicereceipt',
                         'folder_name': 'My Documents',
                         'folder_description': 'I have lots of warez!'};
          var path = '/submission/'+submissionID+'/finalize';
          latenza.ajax({'url': path,
                        'data': JSON.stringify(request),
                        'type': 'POST'
          }).done(function(data){
            debug.write(data, 'POST '+path);
          });

        } else {
          alert("Run create new first!");
        }
      });
    },
    processForm: function(fields, nodeinfo, submission) {
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
            $('.submissionForm button#submit_button').addClass('btn-success');
            $('.submissionForm button#submit_button').removeClass('disabled');
            $('.submissionForm button#submit_button').removeClass('btn-warning');

            $('.submissionForm button#submit_button').click(function(){
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
            $('.submissionForm button#submit_button').addClass('btn-warning');
            $('.submissionForm button#submit_button').addClass('disabled');
            $('.submissionForm button#submit_button').removeClass('btn-success');
          }
        });
    },

    getContextFields: function(context_id) {
      for (var name in nodeinfo.contexts) {
        var context = nodeinfo.contexts[name];
        if (context.id == context_id) {
          return context.fields;
        }
      }
    },

    processContexts: function(contexts) {
      var context_selector = $("#context_selector"),
          context_id, fields;
      context_selector.change(function(){
        context_id = $('#context_selector option:selected')[0].value;
        nodeinfo.context_selected = contexts[0].id;
        fields = getContextFields(context_id);
        processForm(fields);
      });
      for (var i in contexts) {
        // XXX do validation here.
        var context_option = "<option value=" + contexts[i].id + ">" + contexts[i].name + "</option>";
        context_selector.append(context_option);
      };
      return contexts;
    }
  };
});
