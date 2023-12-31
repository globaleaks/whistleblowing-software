import {Injectable} from "@angular/core";
import {Observable, of} from "rxjs";
import {map} from "rxjs/operators";
import {HttpService} from "@app/shared/services/http.service";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {jobResolverModel} from "@app/models/resolvers/job-resolver-model";

@Injectable({
  providedIn: "root"
})
export class JobResolver {
  dataModel: jobResolverModel = new jobResolverModel();

  constructor(private httpService: HttpService, private authenticationService: AuthenticationService) {
  }

  resolve(): Observable<boolean> {
    if (this.authenticationService.session.role === "admin") {
      return this.httpService.requestJobResource().pipe(
        map((response: jobResolverModel) => {
          this.dataModel = response;
          return true;
        })
      );
    }
    return of(true);
  }

}
