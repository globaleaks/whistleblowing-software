angular.module('GLClient.themes', [])
  .factory('Templates', function() {
      var selected_theme = 'default';

      return {
        'home': 'templates/' + selected_theme + '/views/home.html',
        'about': 'templates/' + selected_theme + '/views/about.html',
        'status': 'templates/' + selected_theme + '/views/status.html',
        'submission': {
          'form': 'templates/' + selected_theme + '/views/submission/form.html',
          'main': 'templates/' + selected_theme + '/views/submission/main.html'
        }
      };
    }
);
