import {NgModule} from "@angular/core";
import {CommonModule} from "@angular/common";
import {NgbNavModule, NgbModule} from "@ng-bootstrap/ng-bootstrap";
import {SharedModule} from "@app/shared.module";
import {SidebarComponent} from "@app/pages/admin/sidebar/sidebar.component";
import {RouterModule} from "@angular/router";
import {FormsModule} from "@angular/forms";
import {AdminPreferencesComponent} from "@app/pages/admin/admin-preferences/admin-preferences.component";
import {adminHomeComponent} from "@app/pages/admin/home/admin-home.component";

@NgModule({
  declarations: [
    AdminPreferencesComponent,
    adminHomeComponent,
    SidebarComponent,
  ],
  imports: [
    CommonModule, SharedModule, NgbNavModule, NgbModule, RouterModule, FormsModule
  ],
  exports: [SidebarComponent]
})
export class AdminModule {
}