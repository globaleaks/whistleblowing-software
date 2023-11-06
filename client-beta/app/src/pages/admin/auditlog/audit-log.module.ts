import {NgModule} from "@angular/core";
import {CommonModule} from "@angular/common";
import {AuditLogTab1Component} from "@app/pages/admin/auditlog/auditlog-tab1/audit-log-tab1.component";
import {AuditLogTab2Component} from "@app/pages/admin/auditlog/auditlog-tab2/audit-log-tab2.component";
import {AuditLogTab3Component} from "@app/pages/admin/auditlog/auditlog-tab3/audit-log-tab3.component";
import {AuditLogTab4Component} from "@app/pages/admin/auditlog/auditlog-tab4/audit-log-tab4.component";
import {AuditLogComponent} from "@app/pages/admin/auditlog/audit-log.component";
import {SharedModule} from "@app/shared.module";
import {NgbModule, NgbNavModule} from "@ng-bootstrap/ng-bootstrap";
import {RouterModule} from "@angular/router";
import {FormsModule} from "@angular/forms";
import {NgSelectModule} from "@ng-select/ng-select";
import {AuditLogRoutingModule} from "@app/pages/admin/auditlog/auditlog-routing.module";
import {TranslateModule} from "@ngx-translate/core";

@NgModule({
  declarations: [
    AuditLogTab1Component,
    AuditLogTab2Component,
    AuditLogTab3Component,
    AuditLogTab4Component,
    AuditLogComponent
  ],
  imports: [
    CommonModule,
    AuditLogRoutingModule, SharedModule, NgbNavModule, NgbModule, RouterModule, FormsModule, NgSelectModule, TranslateModule
  ]
})
export class AuditLogModule {
}
