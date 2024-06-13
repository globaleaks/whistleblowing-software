import {NgModule} from "@angular/core";
import {CommonModule} from "@angular/common";
import {SitesComponent} from "@app/pages/admin/sites/sites.component";
import {SitesTab1Component} from "@app/pages/admin/sites/sites-tab1/sites-tab1.component";
import {SitesTab2Component} from "@app/pages/admin/sites/sites-tab2/sites-tab2.component";
import {SitesTabProfilesComponent} from "@app/pages/admin/sites/sites-tab-profiles/sites-tab-profiles.component";
import {SharedModule} from "@app/shared.module";
import {NgbModule, NgbNavModule} from "@ng-bootstrap/ng-bootstrap";
import {RouterModule} from "@angular/router";
import {FormsModule} from "@angular/forms";
import {NgSelectModule} from "@ng-select/ng-select";
import {TranslateModule} from "@ngx-translate/core";
import {SitesRoutingModule} from "@app/pages/admin/sites/sites-routing.module";
import {SiteslistComponent} from "@app/pages/admin/sites/siteslist/siteslist.component";


@NgModule({
  declarations: [
    SitesComponent,
    SitesTab1Component,
    SitesTab2Component,
    SitesTabProfilesComponent,
    SiteslistComponent
  ],
  imports: [
    CommonModule,
    SitesRoutingModule, SharedModule, NgbNavModule, NgbModule, RouterModule, FormsModule, NgSelectModule, TranslateModule
  ]
})
export class SitesModule {
}