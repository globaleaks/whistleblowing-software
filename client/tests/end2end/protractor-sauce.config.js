var browser_capabilities = JSON.parse(process.env.SELENIUM_BROWSER_CAPABILITIES);
browser_capabilities['name'] = 'GlobaLeaks-E2E';
browser_capabilities['tunnel-identifier'] = process.env.TRAVIS_JOB_NUMBER;
browser_capabilities['build'] = process.env.TRAVIS_BUILD_NUMBER;

exports.config = {
  sauceUser: process.env.SAUCE_USERNAME,
  sauceKey: process.env.SAUCE_ACCESS_KEY,
  capabilities: browser_capabilities,

  framework: 'jasmine',

  baseUrl: 'http://localhost:9000/',

  directConnect: false,

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

  jasmineNodeOpts: {
    isVerbose: true,
    includeStackTrace: true,
    showColors: true,
    defaultTimeoutInterval : 180000
  }
};
