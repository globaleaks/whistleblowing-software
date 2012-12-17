// Testacular configuration


// base path, that will be used to resolve files and exclude
basePath = '';


// list of files / patterns to load in the browser
files = [
  JASMINE,
  JASMINE_ADAPTER,
  //'app/scripts/*.js',
  //'app/scripts/**/*.js',

  'app/scripts/vendor/jquery.js',
  'app/scripts/vendor/bootstrap.js',
  'app/scripts/vendor/underscore.js',

  'app/scripts/vendor/jquery.ui.js',
  'app/scripts/vendor/jquery.fileupload.js',
  'app/scripts/vendor/jquery.fileupload-fp.js',
  'app/scripts/vendor/jquery.fileupload-ui.js',

  'app/scripts/vendor/select2/select2.js',

  'app/scripts/vendor/angular.js',
  'app/scripts/vendor/angular-resource.js',
  'app/scripts/vendor/angular-mocks.js',
  'app/scripts/vendor/angular-ui.js',

  'app/scripts/services.js',

  'app/scripts/app.js',
  'app/scripts/ui.js',
  'app/scripts/filters.js',

  'app/scripts/controllers/wizard.js',
  'app/scripts/controllers/latenza.js',
  'app/scripts/controllers/main.js',

  'app/scripts/controllers/page.js',
  'app/scripts/controllers/status.js',

  'app/scripts/controllers/admin/main.js',
  'app/scripts/controllers/admin/receivers.js',
  'app/scripts/controllers/admin/contexts.js',

  'app/scripts/controllers/submission.js',
  'app/scripts/controllers/formbuilder.js',

  'test/spec/**/*.js'
];


// list of files to exclude
exclude = [
  
];


// test results reporter to use
// possible values: dots || progress
reporter = 'progress';


// web server port
port = 8080;


// cli runner port
runnerPort = 9100;


// enable / disable colors in the output (reporters and logs)
colors = true;


// level of logging
// possible values: LOG_DISABLE || LOG_ERROR || LOG_WARN || LOG_INFO || LOG_DEBUG
logLevel = LOG_INFO;


// enable / disable watching file and executing tests whenever any file changes
autoWatch = false;


// Start these browsers, currently available:
// - Chrome
// - ChromeCanary
// - Firefox
// - Opera
// - Safari
// - PhantomJS
browsers = ['PhantomJS'];


// Continuous Integration mode
// if true, it capture browsers, run tests and exit
singleRun = false;
