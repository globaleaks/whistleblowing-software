angular.module('GLClient.themes', [])
  .factory('Templates', function() {
      // XXX do not add the "default" string to this file as it is used by
      // build-custom-glclient.sh for matching.
      var selected_theme = 'default';

      return {
        'home': 'templates/' + selected_theme + '/views/home.html',
        'status': 'templates/' + selected_theme + '/views/status.html',
        'submission': {
          'form': 'templates/' + selected_theme + '/views/submission/form.html',
          'main': 'templates/' + selected_theme + '/views/submission/main.html'
        }
      };
    }
);
