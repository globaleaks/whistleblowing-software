import {Injectable} from "@angular/core";
import {Router, UrlTree} from "@angular/router";
import {Observable} from "rxjs";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {AppConfigService} from "@app/services/root/app-config.service";

@Injectable({
  providedIn: "root"
})
export class CustodianGuard {
  constructor(private appConfigService: AppConfigService, private router: Router, public authenticationService: AuthenticationService) {
  }

  canActivate(): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    if (!this.authenticationService.session || this.authenticationService.session.role !== "custodian") {
      this.router.navigateByUrl("/login").then();
      return false;
    } else {
      this.appConfigService.setPage(this.router.url);
      return true;
    }
  }
}
