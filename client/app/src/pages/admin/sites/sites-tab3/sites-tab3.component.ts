import {Component} from "@angular/core";
import {tenantResolverModel} from "@app/models/resolvers/tenant-resolver-model";
import {HttpService} from "@app/shared/services/http.service";


@Component({
  selector: 'src-sites-tab3',
  templateUrl: './sites-tab3.component.html',
})
export class SitesTab3Component {
  search: string;
  newTenant: { name: string, active: boolean, is_profile:boolean, profile: string, mode: string, subdomain: string } = {
    name: "",
    active: true,
    mode: "default",
    profile: "1000001",
    subdomain: "",
    is_profile: true,
  };
  tenants: tenantResolverModel[];
  showAddTenant: boolean = false;
  itemsPerPage: number = 10;
  currentPage: number = 1;
  indexNumber: number = 0;

  ngOnInit(): void {
    this.httpService.fetchTenant().subscribe(
      tenants => {
        this.tenants = tenants.filter(tenant => tenant.id > 100001);
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
