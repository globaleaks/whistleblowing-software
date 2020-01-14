describe("admin configure, add, and delete contexts", function() {
  it("should configure an existing context", async function() {
    var i, button, input, ctx;
    await browser.setLocation("admin/contexts");

    ctx = element(by.id("context-0"));
    await ctx.element(by.cssContainingText("button", "Edit")).click();

    for (i = 0; i<=2; i++) {
      await ctx.element(by.className("add-receiver-btn")).click();
      button = element(by.id("ReceiverContextAdder")).element(by.model("selected.value"));
      input = button.element(by.css(".ui-select-search"));
      await button.click();
      await input.sendKeys("Recipient" + i.toString());
      await element.all(by.css(".ui-select-choices-row-inner span")).first().click();
    }

    await ctx.element(by.cssContainingText("button", "Advanced settings")).click();

    await ctx.element(by.model("context.allow_recipients_selection")).click();

    await browser.gl.utils.waitUntilPresent(by.model("context.select_all_receivers"));

    await ctx.element(by.model("context.select_all_receivers")).click();

    await ctx.element(by.model("context.enable_messages")).click();
    await ctx.element(by.model("context.enable_rc_to_wb_files")).click();

    // Save the results
    await ctx.element(by.cssContainingText("button", "Save")).click();

    // TODO check if the result was saved
  });

  it("should add new contexts", async function() {
    var add_context = async function(context_name) {
      await element(by.css(".show-add-context-btn")).click();
      await element(by.model("new_context.name")).sendKeys(context_name);
      await element(by.id("add-btn")).click();
      await browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='" + context_name + "']"));
    };

    await add_context("Context 2");
    await add_context("Context 3");
    // TODO check if the contexts were made
  });

  it("should del existing contexts", async function() {
    await element.all((by.cssContainingText("button", "Delete"))).last().click();

    // TODO delete context 2 and 3

    await element(by.id("modal-action-ok")).click();

    // TODO check that the context is actually gone
  });
});
