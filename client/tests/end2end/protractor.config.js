exports.config = {
  framework: 'jasmine',

  baseUrl: 'http://127.0.0.1:8082/',

  troubleshoot: true,
  directConnect: true,

  specs: [
    'test-init.js',
    'test-admin-perform-wizard.js',
    'test-admin-login.js',
    'test-admin-configure-node.js',
    'test-admin-configure-users.js',
    'test-admin-configure-contexts.js',
    'test-receiver-first-login.js',
    'test-globaleaks-process.js'
  ],

  capabilities: {
    'browserName': 'chrome',
    'chromeOptions': {
      prefs: {
        'download': {
          'prompt_for_download': false,
          'default_directory': '/tmp/'
        }
      }
    }
  },

  jasmineNodeOpts: {
    isVerbose: true,
    includeStackTrace: true,
    defaultTimeoutInterval: 60000
  }
};
