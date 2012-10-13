
/*global window */

define(function (require) {
  'use strict';

  var $ = require('jquery'),
      network = require('network'),
      latenza = require('latenza'),
      hogan = require('hogan');

  // Return a function that can be called to do the DOM binding given a
  // jQuery DOM object to use as the parent container.
  return function uiSubmission(parentDom) {

    // Use the body element if no parentDom provided
    parentDom = parentDom || $('body');


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

    function processFields(data) {
        console.log(dummy_requests);
        for (field in data) {
            console.log(data[field]);
        }
        return JSON.stringify(dummy_requests.submissionStatusPost);
    };

    function processForm(form) {
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

        $('#submit_button').click(function(){
          latenza.ajax({'url': '/submission/foobar/status',
                        'data': processFields($(this).serializeArray()),
                        'type': 'POST'
                      }).done(function(data) {
                        var form = $('form');
                        form.hide();
                        var parsed = JSON.parse(data);
                        form.after('<div class="alert">Receipt: '+parsed.receipt+'</div>');
                            // console.log(data);
                      });
          return false;
        });
    };

    function debugDeck() {
        var debug = require('./debug'),
            dummy_requests = require('./dummy/requests'),
            submissionID = null;

        $("#node_button").click(function() {
          latenza.ajax({'url': '/node',
                        'type': 'GET'
          }).done(function(data) {
            submissionID = data['submission_id'];
            debug.write(data, 'GET /node');
          });
        });

        $("#create_new").click(function() {
          latenza.ajax({'url': '/submission',
                        'type': 'GET'
          }).done(function(data) {
            submissionID = data['submission_id'];
            debug.write(data, 'GET /submission');
          });
        });

        $("#send_fields").click(function() {
          var request = dummy_requests.submissionStatusPost;
          if (submissionID) {
            var path = '/submission/'+submissionID+'/status';
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


        $("#status").click(function() {
          var request = dummy_requests.submissionStatusPost;
          if (submissionID) {
            var path = '/submission/'+submissionID+'/status';
            latenza.ajax({'url': path,
                          'type': 'GET'
            }).done(function(data){
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

    latenza.ajax({'url': '/node'}).done(function(data) {
        var formdata = data;
        console.log(formdata);
        processForm(formdata.contexts[0].fields);
        debugDeck();
    });

  };
});
