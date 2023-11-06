import {Injectable} from "@angular/core";

import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {HttpService} from "@app/shared/services/http.service";
import {AuthenticationService} from "@app/services/authentication.service";
import {auditlogResolverModel} from "@app/models/resolvers/auditlog-resolver-model";

@Injectable({
  providedIn: "root"
})
export class AuditLogResolver  {
  dataModel: auditlogResolverModel = new auditlogResolverModel();

  constructor(private httpService: HttpService, private authenticationService: AuthenticationService) {
  }

  resolve(): Observable<boolean> {
    if (this.authenticationService.session.role === "admin") {
      return this.httpService.requestAdminAuditLogResource().pipe(
        switchMap((response: auditlogResolverModel) => {
          this.handleResponse(response);
          return of(true);
        })
      );
    }
    return of(true);
  }


  private handleResponse(response: auditlogResolverModel): void {
    this.dataModel = response;
  }
}
