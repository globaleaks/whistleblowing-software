const { defineConfig } = require('cypress')

module.exports = defineConfig({
  projectId: 'c7x98u',
  chromeWebSecurity: false,
  screenshotsFolder: 'cypress/screenshots/',
  videosFolder: 'cypress/videos',
  defaultCommandTimeout: 30000,
  env: {
    coverage: true,
    init_password: 'Password12345#',
    user_password:
      'ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#',
    field_types: [
      'Single-line text input',
      'Multi-line text input',
      'Selection box',
      'Multiple choice input',
      'Checkbox',
      'Attachment',
      'Terms of service',
      'Date',
      'Date range',
      'Voice',
      'Group of questions',
    ],
    takeScreenshots: true,
  },
  e2e: {
    // We've imported your old cypress plugins here.
    // You may want to clean this up later by importing these.
    setupNodeEvents(on, config) {
      return require('./cypress/plugins/index.js')(on, config)
    },
    baseUrl: 'https://127.0.0.1:8443/',
    supportFile: 'cypress/support/commands.js',
    specPattern: 'cypress/e2e/**/*.{js,jsx,ts,tsx}',
    experimentalMemoryManagement: true,
    numTestsKeptInMemory: 1,
    video: false
  },
})
