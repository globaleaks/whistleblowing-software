define(function (require) {
  'use strict';

  var $ = require('jquery'),
      network = require('network'),
      latenza = require('latenza'),
      hogan = require('hogan'),
      requests = {},
      nodeinfo = {};

  requests.submission = require('./requests/submission');
  requests.node = require('./requests/node');


  // Return a function that can be called to do the DOM binding given a
  // jQuery DOM object to use as the parent container.
  return function uiSubmission(parentDom) {

    // Use the body element if no parentDom provided
    parentDom = parentDom || $('body');

    function debugDeck() {
        var debug = require('./debug'),
            dummy_requests = require('./dummy/requests'),
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
    };


    function renderTemplate(template, data) {
        if (data.help) {
            template += '<span class="help-block">{{help}}</span>'
        }
        var cTemplate = hogan.compile(template);
        var rendered = cTemplate.render(data);
        // console.log(rendered);
        return rendered;
    };

    var process = {
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

    function incompleteForm() {
    };

    function submitForm(data) {
        // console.log(data);
        var x,
            form = $(data.target.parentElement);

        var inputs = form.find('input');

        for (x in inputs) {
            // console.log(inputs[x]);
        };
        return false;
    };

    function processFields(form) {
      var data = form.serializeArray(),
          fields = {};
      for (var field in data) {
        fields[data[field].name] = data[field].value;
      }
      return fields;
    };

    function showReceipt(receipt_id) {
      $('.submissionForm').hide();
      $('.submissionContainer').append("<h2>Here is your receipt</h2>");
      $('.submissionContainer').append("<h3>"+receipt_id+"</h3>");
      $('.submissionContainer').append("<a href='/tip/"+receipt_id+"'>debug link</a>");
    };

    function processForm(form) {
        $('.submissionFormLeft')[0].innerHTML = "";
        $('.submissionFormRight')[0].innerHTML = "";
        $('.submissionForm button').remove();

        var x, target,
            allowed_types = ['string', 'text','checkbox', 'radio'];
        for (x in form) {
          // console.log(form[x].type);
          if (allowed_types.indexOf(form[x].type) != -1) {
            if ((x % 2) == 0) {
              target = $('.submissionFormLeft');
            } else {
              target = $('.submissionFormRight');
            }
            target.append(process[form[x].type](form[x]));
          }
        };
        $('.submissionForm').append('<button id="submit_button">Submit</button>');

        // XXX refactor this to remove this nesting insanity!
        $('#submit_button').click(function(){
          requests.submission.root().done(function(data) {
            var fields = processFields($('.submissionForm'));
            requests.submission.status_post(data['submission_id'],
                  {'fields': fields,
                   'context_selected': nodeinfo.context_selected}).done(function(args){
                     var proposed_receipt = "ididntchangeit",
                         folder_name = "foldername",
                         folder_description = "folderdesc";
                     requests.submission.finalize_post(data['submission_id'], proposed_receipt,
                                    folder_name, folder_description).done(function(data){
                                      showReceipt(data.receipt);
                                    });
            });
          });
          return false;
        });
    };

    function getContextFields(context_id) {
      for (var name in nodeinfo.contexts) {
        var context = nodeinfo.contexts[name];
        if (context.id == context_id) {
          return context.fields;
        }
      }
    };

    function processContexts(contexts) {
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
    };

    requests.node.root().done(function(data) {
        var contexts;
        nodeinfo = data;
        nodeinfo.contexts = processContexts(nodeinfo.contexts);
        nodeinfo.context_selected = nodeinfo.contexts[0].id;
        processForm(nodeinfo.contexts[0].fields);
        debugDeck();
    });

  };
});
