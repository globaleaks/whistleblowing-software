import {NgModule} from "@angular/core";
import {RouterModule, Routes} from "@angular/router";
import {ForcedTwoFactorComponent} from "@app/pages/action/forced-two-factor/forced-two-factor.component";
import {ForcePasswordChangeComponent} from "@app/pages/action/force-password-change/force-password-change.component";

const routes: Routes = [
  {
    path: "forcedtwofactor",
    component: ForcedTwoFactorComponent,
    pathMatch: "full",
    data: {pageTitle: "Password reset"},
  }, {
    path: "forcedpasswordchange",
    component: ForcePasswordChangeComponent,
    pathMatch: "full",
    data: {pageTitle: "Password reset"},
  }

];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class ActionRoutingModule {
}