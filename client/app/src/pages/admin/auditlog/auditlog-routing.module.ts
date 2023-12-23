import {NgModule} from "@angular/core";
import {RouterModule, Routes} from "@angular/router";
import {AuditLogComponent} from "@app/pages/admin/auditlog/audit-log.component";

const routes: Routes = [
  {
    path: "",
    component: AuditLogComponent,
    pathMatch: "full",
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AuditLogRoutingModule {
}
