import {Component, OnInit} from "@angular/core";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-sites-tab1",
  templateUrl: "./sites-tab1.component.html"
})
export class SitesTab1Component implements OnInit {
  search: any;
  newTenant: any = {};
  tenants: any = [];
  showAddTenant = false;
  itemsPerPage: number = 10;
  currentPage: number = 1;

  ngOnInit(): void {
    this.newTenant.active = true;
    this.newTenant.name = "";
    this.newTenant.mode = "default";
    this.newTenant.subdomain = "";
    this.httpService.fetchTenant().subscribe(
      tenant => {
        this.tenants = tenant;
      }
    );
  }

  toggleAddTenant() {
    this.showAddTenant = !this.showAddTenant;
  }

  constructor(private httpService: HttpService, private utilsService: UtilsService) {
  }

  addTenant() {
    this.httpService.addTenant(this.newTenant).subscribe(_ => {
      this.utilsService.reloadCurrentRoute();
    });
  }
}