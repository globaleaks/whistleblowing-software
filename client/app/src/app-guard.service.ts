import {Injectable} from "@angular/core";
import {Router, UrlTree} from "@angular/router";
import {Observable} from "rxjs";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {AppDataService} from "@app/app-data.service";

@Injectable({
  providedIn: "root"
})
export class SessionGuard  {
  constructor(private router: Router, private appDataService: AppDataService, public authenticationService: AuthenticationService) {
  }

  canActivate(): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    if (!this.authenticationService.session) {
      this.router.navigateByUrl("/login").then();
      return false;
    } else {
      this.appDataService.page = this.router.url;
      return true;
    }
  }
}
