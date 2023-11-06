import {Injectable} from "@angular/core";
import { Router, UrlTree } from "@angular/router";
import {Observable} from "rxjs";
import {AuthenticationService} from "@app/services/authentication.service";
import {AppDataService} from "@app/app-data.service";

@Injectable({
  providedIn: "root"
})
export class CustodianGuard  {
  constructor(private router: Router, private appDataService: AppDataService, public authenticationService: AuthenticationService) {
  }

  canActivate(): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    if (!this.authenticationService.session || this.authenticationService.session.role !== "custodian") {
      this.router.navigateByUrl("/login").then();
      return false;
    } else {
      this.appDataService.page = this.router.url;
      return true;
    }
  }
}
