// ~ router.js ~
define([
  'jquery',
  'underscore',
  'backbone',
  'views/submission/main',
  'views/submission/new',
  'views/admin/main',
  'views/status/list',
  'views/status/tip'
], function($, _, Backbone, mainSubmissionView, newSubmissionView, mainAdminView){
  var AppRouter = Backbone.Router.extend({
    routes: {
      // Define some URL routes
      'submit': 'newSubmission',
      'admin': 'showAdmin',
      
      // Default
      '*actions': 'defaultAction'
    },
    // Load the page for the new submission
    newSubmission: function(){
    	newSubmissionView.render();
    },
    
    // Show the node administration interface
    showAdmin: function(){
    	mainAdminView.render();
    },
    
    // No matched rules go to the default home page
    defaultAction: function(actions){
    	mainSubmissionView.render(); 
    }
  });

  var initialize = function(){
    var app_router = new AppRouter;
    Backbone.history.start();
  };
  return { 
    initialize: initialize
  };
});
