define(['jquery', 'utils/util'], function($, utils) {
  return {
    processStatusGet: function(data) {
      console.log("Processing " );
      console.log(data);
      var safe_data = {};
      safe_data['fields'] = [];
      for (var name in data.fields) {
        var value, safe_name, safe_value;

        value = data.fields[name];

        console.log(name + " | " + value);
        safe_name = utils.htmlEntities(name);
        if (value) {
          safe_value = utils.htmlEntities(value);
          safe_data['fields'].push({'name': safe_name, 'value': safe_value});
        } else {
          console.log("skipping");
        }

        console.log(name + " | " + value);
      }
      // XXX properly parse this
      safe_data['folders'] = data.folders;
      safe_data['receivers'] = data.receivers;
      safe_data['comments'] = data.comments;
      return safe_data;
    },


  }
});

