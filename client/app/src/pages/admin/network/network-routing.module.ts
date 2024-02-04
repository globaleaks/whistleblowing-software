import {NgModule} from "@angular/core";
import {RouterModule, Routes} from "@angular/router";
import {NetworkComponent} from "@app/pages/admin/network/network.component";

const routes: Routes = [
  {
    path: "",
    component: NetworkComponent,
    pathMatch: "full",
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class NetworkRoutingModule {
}