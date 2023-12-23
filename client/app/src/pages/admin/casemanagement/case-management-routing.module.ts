import {NgModule} from "@angular/core";
import {RouterModule, Routes} from "@angular/router";
import {CaseManagementComponent} from "@app/pages/admin/casemanagement/case-management.component";

const routes: Routes = [
  {
    path: "",
    component: CaseManagementComponent,
    pathMatch: "full",
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class CaseManagementRoutingModule {
}
