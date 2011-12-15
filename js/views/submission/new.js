// ~ views/submission/new ~
define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/submission/new.html'
], function($, _, Backbone, newSubmissionTemplate){
  var newSubmissionView = Backbone.View.extend({
	    el: $("#content"),
	    initialize: function(){
	    	// Do something...
	    },
	    testBind: function(model) {
	    	// Do something else..
	    },
	    
	    render: function(){
	    	var data = {};
	    	var compiledTemplate = _.template(newSubmissionTemplate, data);
	    	this.el.html(compiledTemplate);
	    }
  });
  return new newSubmissionView;
});

