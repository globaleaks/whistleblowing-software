define(['jquery'], function($) {
  return {
    write: function(data, name){
      $(".debug-header").modal();
      if (typeof(data) == "object") {
        json_data = JSON.stringify(data, undefined, 2);

        data = '<pre>'+json_data+'</pre>';

      }
      var msg = '<li><span class="label label-info">'+name+'</span> ';
      msg += data + '</li>';
      $("#debug-header-loglist").append(msg);
    }
  };
});
