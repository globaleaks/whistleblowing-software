// ~ views/admin/main ~
define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/admin/main.html'
], function($, _, Backbone, mainAdminTemplate){
  var mainAdminView = Backbone.View.extend({
	    el: $("#content"),
	    render: function(){
			var data = {};
			var compiledTemplate = _.template(mainAdminTemplate, data);
			this.el.html(compiledTemplate);
	    }
  });
  return new mainAdminView;
});

