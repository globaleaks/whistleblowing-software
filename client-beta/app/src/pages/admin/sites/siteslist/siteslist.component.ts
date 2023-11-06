import {Component, Input} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import {DeleteConfirmationComponent} from "@app/shared/modals/delete-confirmation/delete-confirmation.component";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {AppConfigService} from "@app/services/app-config.service";

@Component({
  selector: "src-siteslist",
  templateUrl: "./siteslist.component.html"
})
export class SiteslistComponent {
  @Input() tenant: any;
  @Input() tenants: any;
  @Input() index: any;
  editing = false;

  constructor(private appConfigService: AppConfigService, protected appDataService: AppDataService, private modalService: NgbModal, private httpService: HttpService, private utilsService: UtilsService) {
  }

  toggleActivation(event: Event): void {
    event.stopPropagation();
    this.tenant.active = !this.tenant.active;

    const url = "api/admin/tenants/" + this.tenant.id;
    this.httpService.requestUpdateTenant(url, this.tenant).subscribe(_ => {
    });
  }

  isRemovableTenant(): boolean {
    return this.tenant.id !== 1;
  }

  saveTenant() {
    const url = "api/admin/tenants/" + this.tenant.id;
    this.httpService.requestUpdateTenant(url, this.tenant).subscribe(_ => {
      this.utilsService.reloadCurrentRoute();
    });
  }

  deleteTenant(event: any, tenant: any) {
    event.stopPropagation();
    this.openConfirmableModalDialog(tenant, "").then();
  }

  configureTenant($event: Event, tid: number): void {
    $event.stopPropagation();

    this.httpService.requestTenantSwitch("api/auth/tenantauthswitch/" + tid).subscribe(res => {
      window.open(res.redirect);
    });
  }

  openConfirmableModalDialog(arg: any, scope: any): Promise<any> {
    scope = !scope ? this : scope;
    const modalRef = this.modalService.open(DeleteConfirmationComponent);
    modalRef.componentInstance.arg = arg;
    modalRef.componentInstance.scope = scope;
    modalRef.componentInstance.confirmFunction = () => {

      const url = "api/admin/tenants/" + arg.id;
      return this.httpService.requestDeleteTenant(url).subscribe(_ => {
         this.utilsService.deleteResource(this.tenants,arg);
      });
    };
    return modalRef.result;
  }

  toggleEditing(event: Event): void {
    event.stopPropagation();
    this.editing = !this.editing;
  }
}