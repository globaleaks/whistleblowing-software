import {NgModule} from "@angular/core";
import {RouterModule, Routes} from "@angular/router";
import {PreferencesComponent} from "@app/shared/partials/preferences/preferences.component";
import {HomeComponent} from "@app/pages/custodian/home/home.component";
import {SettingsComponent} from "@app/pages/custodian/settings/settings.component";
import {IdentityAccessRequestsComponent} from "@app/pages/custodian/identity-access-requests/identity-access-requests.component";

const routes: Routes = [
  {
    path: "preferences",
    component: PreferencesComponent,
    pathMatch: "full",
    data: {pageTitle: "Preferences"},
  },
  {
    path: "home",
    component: HomeComponent,
    pathMatch: "full",
    data: {pageTitle: "Home"},
  },
  {
    path: "",
    component: HomeComponent,
    pathMatch: "full",
    data: {pageTitle: "Home"},
  },
  {
    path: "settings",
    component: SettingsComponent,
    pathMatch: "full",
    data: {pageTitle: "Sites"},
  },
  {
    path: "requests",
    component: IdentityAccessRequestsComponent,
    pathMatch: "full",
    data: {pageTitle: "Requests"},
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class CustodianRoutingModule {
}
