/**
 * @type {Cypress.PluginConfig}
 */
import * as fs from 'fs'
import * as registerCodeCoverageTasks from "@cypress/code-coverage/task";

export default (on, config) => {

  on('before:browser:launch', (browser = {}, launchOptions) => {
    launchOptions.preferences.width = 1280;
    launchOptions.preferences.height = 1250;
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
