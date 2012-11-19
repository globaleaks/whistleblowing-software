/*global window */

GLClient.controller('ReceiverCtrl', function($scope) {
  for (var i = 0;i < 120;i++) {
    var parity = (i % 2 == 0) ? 'even' : 'odd';

    // XXX This is just some random junk data
    var name = "Antani Sblinda",
      views = Math.round(Math.random()*1000)*3,
      diff = Math.round(Math.random()*10);

    var date = new Date();
    date.setDate(-1*diff*100);

    var my_views = views - Math.round(diff/2);
    var downloads = views - Math.round(diff/4);
    var pertinence = diff;
    $scope.tips.push({'name': name, 'date': date, 'my_views': my_views,
      'downloads': downloads, 'pertinence': pertinence, 'parity': parity});
  }
  $('#tipList').dataTable( {
      "sDom": "<'row'<'span4'l><'span5'f>r>t<'row'<'span4'i><'span5'p>>",
      "sPaginationType": "bootstrap",
      "oLanguage": {
        "sLengthMenu": "_MENU_ records per page"
      }
  });
});

