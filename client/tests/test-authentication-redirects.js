describe("perform rediects on authenticated pages", function() {
  it("test rtip redirect to login page", async function() {
    await browser.get("/#/status/2f0535eb-9710-47e5-8082-5f882d4ec770");

    await browser.gl.utils.waitForUrl("/login?src=%2Fstatus%2F2f0535eb-9710-47e5-8082-5f882d4ec770");
  });

  it("test admin redirect to login page", async function() {
    await browser.get("/#/admin/advanced_settings");

    await browser.gl.utils.waitForUrl("/admin?src=%2Fadmin%2Fadvanced_settings");
  });

  it("test custodian redirect to login page", async function() {
    await browser.get("/#/custodian/identityaccessrequests");

    await browser.gl.utils.waitForUrl("/login?src=%2Fcustodian%2Fidentityaccessrequests");
  });
});
