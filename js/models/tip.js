// ~ models/tip ~
define([
  'jquery',
  'backbone'
], function(_, Backbone){
  var tipModel = Backbone.Model.extend({
    defaults: {
      name: ""
    }
  });
  return tipModel;
});
