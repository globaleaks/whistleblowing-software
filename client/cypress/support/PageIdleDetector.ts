export class PageIdleDetector {
  private defaultOptions = {timeout: 60000};

  constructor() {
  }

  waitForPageToBeIdle() {
    this.waitForPageToLoad();
    this.waitForAngularRequestsToComplete();
    this.waitForAngularDigestCycleToComplete();
    this.waitForAnimationsToStop();
  }

  private waitForPageToLoad(options = this.defaultOptions) {
    cy.document(options).should((myDocument) => {
      expect(myDocument.readyState, "WaitForPageToLoad").to.be.oneOf([
        "interactive",
        "complete"
      ]);
    });
  }

  private waitForAngularRequestsToComplete(options = this.defaultOptions) {
    cy.window(options).should((myWindow) => {
      if (!!myWindow.angular) {
        expect(
          this.numberOfPendingAngularRequests(myWindow),
          "WaitForAngularRequestsToComplete"
        ).to.have.length(0);
      }
    });
  }

  private waitForAngularDigestCycleToComplete(options = this.defaultOptions) {
    cy.window(options).should((myWindow) => {
      if (!!myWindow.angular) {
        expect(
          this.angularRootScopePhase(myWindow),
          "WaitForAngularDigestCycleToComplete"
        ).to.be.null;
      }
    });
  }

  private waitForAnimationsToStop(options = this.defaultOptions) {
    cy.get(":animated", options).should("not.exist");
  }

  private getInjector(myWindow: any) {
    return myWindow.angular.element(myWindow.document.body).injector();
  }

  private numberOfPendingAngularRequests(myWindow: any) {
    return this.getInjector(myWindow).get("$http").pendingRequests;
  }

  private angularRootScopePhase(myWindow: any) {
    return this.getInjector(myWindow).get("$rootScope").$$phase;
  }

}
