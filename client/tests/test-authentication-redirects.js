describe("perform redirects on authenticated pages", function() {
  it("test redirect to login page using /login url", async function() {
    await browser.get("/login");
    await browser.gl.utils.waitForUrl("/login");
  });

  it("test redirect to login page using /admin url", async function() {
    await browser.get("/admin");
    await browser.gl.utils.waitForUrl("/admin");
  });

  it("test rtip redirect to login page", async function() {
    await browser.get("/#/status/2f0535eb-9710-47e5-8082-5f882d4ec770");

    await browser.gl.utils.waitForUrl("/login");
  });

  it("test admin redirect to login page", async function() {
    await browser.get("/#/admin/advanced");

    await browser.gl.utils.waitForUrl("/login");
  });
});
