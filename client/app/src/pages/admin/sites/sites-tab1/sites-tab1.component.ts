import {Component, OnInit} from "@angular/core";
import {tenantResolverModel} from "@app/models/resolvers/tenant-resolver-model";
import {HttpService} from "@app/shared/services/http.service";

@Component({
  selector: "src-sites-tab1",
  templateUrl: "./sites-tab1.component.html"
})
export class SitesTab1Component implements OnInit {
  search: string;
  newTenant: { name: string, active: boolean, mode: string,is_profile:boolean, default_profile: string, subdomain: string } = {
    name: "",
    active: true,
    mode: "default",
    default_profile: "default",
    subdomain: "",
    is_profile: false,
  };
  tenants: tenantResolverModel[];
  profileTenants: tenantResolverModel[];
  showAddTenant: boolean = false;
  itemsPerPage: number = 10;
  currentPage: number = 1;
  indexNumber: number = 0;

  ngOnInit(): void {
    this.fetchTenants();
  }

  fetchTenants() {
    this.httpService.fetchTenant().subscribe(
      tenants => {
        this.tenants = tenants.filter(tenant => tenant.id < 1000001);
        this.profileTenants = tenants.filter(tenant => tenant.id > 1000001);
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
      this.newTenant.default_profile = "default";
    });
  }
}