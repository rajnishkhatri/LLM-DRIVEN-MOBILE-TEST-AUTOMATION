// Exported from Perfecto scriptless test ACC-1042 via rel-26.2 export-to-Appium-JS.
// This is the audit bridge: the live artifact in Perfecto is interpreted intent (black box),
// but on export it becomes inspectable, committed Appium JavaScript that re-enters the spine's
// static gate. The export is what makes O4 audit-credible; without it, O4 is O2-with-a-vendor.

const { remote } = require('webdriverio');
const assert = require('assert');

async function loginShowsWelcome(driver) {
  // step 1-2: username
  const username = await driver.$('~usernameField');   // accessibility id, resolved at export time
  await username.click();
  await username.setValue(process.env.VAULT_USER_QA);

  // step 3-4: password
  const password = await driver.$('~passwordField');
  await password.click();
  await password.setValue(process.env.VAULT_PASS_QA);

  // step 5: login
  const login = await driver.$('~loginButton');
  await login.click();

  // step 6: assert welcome
  const banner = await driver.$('~welcomeBanner');
  const text = await banner.getText();
  assert.strictEqual(text, 'Welcome, QA User');
}

module.exports = { loginShowsWelcome };
