import {Injectable} from "@angular/core";

import {Observable, of} from "rxjs";
import {switchMap} from "rxjs/operators";
import {HttpService} from "@app/shared/services/http.service";
import {AuthenticationService} from "@app/services/authentication.service";
import {contextResolverModel} from "@app/models/resolvers/context-resolver-model";

@Injectable({
  providedIn: "root"
})
export class ContextsResolver  {
  dataModel: contextResolverModel = new contextResolverModel();

  constructor(private httpService: HttpService, private authenticationService: AuthenticationService) {
  }

  resolve(): Observable<boolean> {
    if (this.authenticationService.session.role === "admin") {
      return this.httpService.requestContextsResource().pipe(
        switchMap((response: contextResolverModel) => {
          this.dataModel = response;
          return of(true);
        })
      );
    }

    return of(true);
  }

}
