import {Component, OnInit} from "@angular/core";
import {tenantResolverModel} from "@app/models/resolvers/tenant-resolver-model";
import {HttpService} from "@app/shared/services/http.service";

@Component({
  selector: "src-sites-tab1",
  templateUrl: "./sites-tab1.component.html"
})
export class SitesTab1Component implements OnInit {
  search: string;
  newTenant: { name: string, active: boolean, mode: string, subdomain: string } = {
    name: "",
    active: true,
    mode: "default",
    subdomain: ""
  };
  tenants: tenantResolverModel[];
  showAddTenant: boolean = false;
  itemsPerPage: number = 10;
  currentPage: number = 1;

  ngOnInit(): void {
    this.httpService.fetchTenant().subscribe(
      tenant => {
        this.tenants = tenant;
      }
    );
  }

  toggleAddTenant() {
    this.showAddTenant = !this.showAddTenant;
  }

  constructor(private httpService: HttpService) {
  }

  addTenant() {
    this.httpService.addTenant(this.newTenant).subscribe(res => {
      this.tenants.push(res);
      this.newTenant.name = "";
    });
  }
}