import {NgModule} from "@angular/core";
import {CommonModule} from "@angular/common";
import {RouterModule} from "@angular/router";
import {TranslateModule} from "@ngx-translate/core";
import {SharedModule} from "@app/shared.module";
import {FormsModule} from "@angular/forms";
import {NgbDatepickerModule, NgbDropdownModule, NgbModule, NgbNavModule} from "@ng-bootstrap/ng-bootstrap";
import {NgMultiSelectDropDownModule} from "ng-multiselect-dropdown";
import {HomeComponent} from "@app/pages/custodian/home/home.component";
import {SettingsComponent} from "@app/pages/custodian/settings/settings.component";
import {SidebarComponent} from "@app/pages/custodian/sidebar/sidebar.component";
import {
  IdentityAccessRequestsComponent
} from "@app/pages/custodian/identity-access-requests/identity-access-requests.component";
import {SettingsModule} from "@app/pages/admin/settings/settings.module";


@NgModule({
  declarations: [
    HomeComponent,
    SettingsComponent,
    SidebarComponent,
    IdentityAccessRequestsComponent
  ],
  imports: [
    CommonModule, RouterModule, TranslateModule, SharedModule, FormsModule,
    NgbModule, NgbNavModule,
    NgbDatepickerModule, NgbDropdownModule, NgMultiSelectDropDownModule.forRoot(), SettingsModule
  ],
  exports: [SidebarComponent]
})
export class CustodianModule {
}
