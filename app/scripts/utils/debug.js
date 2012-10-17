define(['libs/jquery', 'dummy/requests',
        'requests/node', 'requests/submission'],
        function($, dummy_requests, requests_node, requests_submission) {

  function debugWrite(data, name){
      $(".debug-header").modal();
      if (typeof(data) == "object") {
        json_data = JSON.stringify(data, undefined, 2);

        data = '<pre>'+json_data+'</pre>';

      }
      var msg = '<li><span class="label label-info">'+name+'</span> ';
      msg += data + '</li>';
      $("#debug-header-loglist").append(msg);
  }

  return {

    debugDeck: function() {
      var submissionID = null;

      $("#node_button").click(function() {
        latenza.ajax({'url': '/node',
                      'type': 'GET'
        }).done(function(data) {
          debugWrite(data, 'GET /node');
        });
      });

      $("#create_new").click(function() {
        requests_submission.root().done(function(data) {
                submissionID = data['submission_id'];
                debugWrite(data, 'GET /submission');
        });
      });

      $("#send_fields").click(function() {
        if (submissionID) {
          var fields = {"FieldA": "hello", "FieldB": "world!"};
          var path = '/submission/'+submissionID+'/status';
          requests_submission.status_post(submissionID, {'fields': fields}).done(function(data){
            debugWrite(data, 'POST '+path);
          });

        } else {
          alert("Run create new first!");
        }
      });

      $("#select_context").click(function() {
        if (submissionID) {
          var path = '/submission/'+submissionID+'/status';
          requests_node.root().done(function(nodeinfo) {
            var context_selected = nodeinfo.contexts[0].id;
            requests_submission.status_post(submissionID, {'context_selected':
                              context_selected}).done(function(data){
              debugWrite(data, 'POST '+path);
            });
          });

        } else {
          alert("Run create new first!");
        }
      });

      $("#status").click(function() {
        var request = dummy_requests.submissionStatusPost;
        if (submissionID) {
          var path = '/submission/'+submissionID+'/status';
          requests_submission.status_get(submissionID).done(function(data){
            debugWrite(data, 'GET '+path);
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
            debugWrite(data, 'POST '+path);
          });

        } else {
          alert("Run create new first!");
        }
      });
    }
  };
});
