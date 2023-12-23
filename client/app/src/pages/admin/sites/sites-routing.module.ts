import {NgModule} from "@angular/core";
import {RouterModule, Routes} from "@angular/router";
import {SitesComponent} from "@app/pages/admin/sites/sites.component";

const routes: Routes = [
  {
    path: "",
    component: SitesComponent,
    pathMatch: "full",
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class SitesRoutingModule {
}