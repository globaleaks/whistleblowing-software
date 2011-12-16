// ~ models/tip ~
define([
  'jquery',
  'backbone'
], function(_, Backbone){
  var tipModel = Backbone.Model.extend({
	
    initialize: function() {
    	// create the tip
    	content = {};
    	comments = {};
    	
    	// If we are instantiating a Tip with an id
    	// try fetching it's value from the remote 
    	// backend
    	if(this.get("id")){
    		this.fetch(this.get("id"));
    	}
    	
    },

    // Push it to the remote backend
  	submit: function(){
  		// Fill me up with joy!
  	},
    
	// Delete it from the remote backend
    remove: function(){
    	// Make me a happy function
    },

    // The Tip is being downloaded
    download: function(){
    	// I need your code!
    },

    // The Tip is being accessed
    access: function() {
    	// An empty function is a sad function!
    },

	// Add a comment to the Tip
    comment: function() {
    	// 8====D
    }
  
  });
  return tipModel;
});
