import {NgModule} from "@angular/core";
import {CommonModule} from "@angular/common";
import {NetworkRoutingModule} from "@app/pages/admin/network/network-routing.module";
import {NetworkComponent} from "@app/pages/admin/network/network.component";
import {FormsModule} from "@angular/forms";
import {RouterModule} from "@angular/router";
import {NgbNavModule, NgbModule} from "@ng-bootstrap/ng-bootstrap";
import {NgSelectModule} from "@ng-select/ng-select";
import {SharedModule} from "@app/shared.module";
import {HttpsComponent} from "@app/pages/admin/network/https/https.component";
import {TorComponent} from "@app/pages/admin/network/tor/tor.component";
import {AccessControlComponent} from "@app/pages/admin/network/access-control/access-control.component";
import {UrlRedirectsComponent} from "@app/pages/admin/network/url-redirects/url-redirects.component";
import {HttpsSetupComponent} from "@app/pages/admin/network/https-setup/https-setup.component";
import {HttpsFilesComponent} from "@app/pages/admin/network/https-files/https-files.component";
import {HttpsStatusComponent} from "@app/pages/admin/network/https-status/https-status.component";
import {HttpsCsrGenComponent} from "@app/pages/admin/network/https-csr-gen/https-csr-gen.component";


@NgModule({
  declarations: [
    NetworkComponent,
    HttpsComponent,
    TorComponent,
    AccessControlComponent,
    UrlRedirectsComponent,
    HttpsSetupComponent,
    HttpsFilesComponent,
    HttpsStatusComponent,
    HttpsCsrGenComponent
  ],
  imports: [
    CommonModule,
    NetworkRoutingModule, SharedModule, NgbNavModule, NgbModule, RouterModule, FormsModule, NgSelectModule,
  ]
})
export class NetworkModule {
}