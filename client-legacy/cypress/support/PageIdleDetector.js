// source: chrisp_68 @ https://stackoverflow.com/questions/50525143/how-do-you-reliably-wait-for-page-idle-in-cypress-io-test
export class PageIdleDetector {
  defaultOptions = { timeout: 60000 }

  WaitForPageToBeIdle() {
    this.WaitForPageToLoad()
    this.WaitForAngularRequestsToComplete()
    this.WaitForAngularDigestCycleToComplete()
    this.WaitForAnimationsToStop()
  }

  WaitForPageToLoad(options = this.defaultOptions) {
    cy.document(options).should(myDocument => {
      expect(myDocument.readyState, "WaitForPageToLoad").to.be.oneOf([
        "interactive",
        "complete"
      ])
    })
  }

  WaitForAngularRequestsToComplete(options = this.defaultOptions) {
    cy.window(options).should(myWindow => {
      if (!!myWindow.angular) {
        expect(
          this.NumberOfPendingAngularRequests(myWindow),
          "WaitForAngularRequestsToComplete"
        ).to.have.length(0)
      }
    })
  }

  WaitForAngularDigestCycleToComplete(options = this.defaultOptions) {
    cy.window(options).should(myWindow => {
      if (!!myWindow.angular) {
        expect(
          this.AngularRootScopePhase(myWindow),
          "WaitForAngularDigestCycleToComplete"
        ).to.be.null
      }
    })
  }

  WaitForAnimationsToStop(options = this.defaultOptions) {
    cy.get(":animated", options).should("not.exist")
  }

  getInjector(myWindow) {
    return myWindow.angular.element(myWindow.document.body).injector()
  }

  NumberOfPendingAngularRequests(myWindow) {
    return this.getInjector(myWindow).get("$http").pendingRequests
  }

  AngularRootScopePhase(myWindow) {
    return this.getInjector(myWindow).get("$rootScope").$$phase
  }
}

