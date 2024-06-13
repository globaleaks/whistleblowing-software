import {Component, OnInit} from "@angular/core";
import {tenantResolverModel} from "@app/models/resolvers/tenant-resolver-model";
import {HttpService} from "@app/shared/services/http.service";

@Component({
  selector: "src-sites-tab-profiles",
  templateUrl: "./sites-tab-profiles.component.html"
})
export class SitesTabProfilesComponent implements OnInit {
  search: string;
  newTenant: { name: string, active: boolean, mode: string, is_profile: boolean, profile_tenant_id: number | null , subdomain: string } = {
    name: "",
    active: true,
    mode: "default",
    is_profile: true,
    profile_tenant_id: 1,
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