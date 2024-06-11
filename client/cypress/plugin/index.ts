/**
 * @type {Cypress.PluginConfig}
 */
import * as fs from 'fs'
import * as registerCodeCoverageTasks from "@cypress/code-coverage/task";

export default (on, config) => {
  on('before:browser:launch', (browser: Cypress.Browser, launchOptions: Cypress.BrowserLaunchOptions) => {
    if (browser.family === 'chromium') {
      launchOptions.args.push('--window-size=1920,1080')
      launchOptions.args.push('--force-device-scale-factor=1');
      launchOptions.args.push('--force-color-profile=srgb');
      launchOptions.args.push('--disable-low-res-tiling');
      launchOptions.args.push('--disable-smooth-scrolling');
    }
    return launchOptions;
  });

  on('after:screenshot', (details) => {
    if (details.path.includes('failed')) {
      return;
    }

    return new Promise((resolve, reject) => {
      let newPath = __dirname + "/../../../documentation/images/" + details.path.split('/').slice(-2).join('/')

      fs.copyFile(details.path, newPath, (err) => {
        if (err) return reject(err)

        resolve({ path: newPath })
      })
    })
  })

  return registerCodeCoverageTasks(on, config);
};
