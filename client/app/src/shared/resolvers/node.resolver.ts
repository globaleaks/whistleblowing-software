import {Injectable} from "@angular/core";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {Observable, of} from "rxjs";
import {HttpService} from "@app/shared/services/http.service";
import {nodeResolverModel} from "@app/models/resolvers/node-resolver-model";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {map} from "rxjs/operators";

@Injectable({
  providedIn: "root"
})
export class NodeResolver  {
  dataModel: nodeResolverModel = new nodeResolverModel();

  constructor(private httpService: HttpService, private authenticationService: AuthenticationService, private preferenceResolver: PreferenceResolver) {
  }

  resolve(): Observable<boolean> {
    if (this.authenticationService.session.role === "admin" || ( this.authenticationService.session.role === "receiver" && this.preferenceResolver.dataModel.can_edit_general_settings)) {
      return this.httpService.requestNodeResource().pipe(
        map((response: nodeResolverModel) => {
          this.dataModel = response;
          return true;
        })
      );
    }
    return of(true);
  }
}
