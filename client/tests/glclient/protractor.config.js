exports.config = {
  seleniumAddress: 'http://localhost:4444/wd/hub',

  troubleshoot: true,
  directConnect: true,

  specs: [
    'test-001-wizard.js',
    'test-002-grant-tor2web-permissions.js'
  ],

  capabilities: {
    'browserName': 'firefox'
  },

  framework: 'jasmine2',

  jasmineNodeOpts: {
   isVerbose: true,
   //defaultTimeoutInterval: 30000
  },

  baseUrl: 'http://127.0.0.1:8082/',

  onPrepare: function() {
     browser.driver.manage().window().setSize(1200, 600);
  },
}


