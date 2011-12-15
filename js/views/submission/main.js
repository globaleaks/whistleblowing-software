// ~ main.js ~
define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/submission/main.html'
], function($, _, Backbone, mainSubmissionTemplate){
  var mainSubmissionView = Backbone.View.extend({
	    el: $("#content"),
	    render: function(){
	      this.el.html(mainSubmissionTemplate);
	    }
  });
  return new mainSubmissionView;
});

