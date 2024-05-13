import {Injectable} from "@angular/core";
import {Observable, of} from "rxjs";
import {HttpService} from "@app/shared/services/http.service";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {map} from "rxjs/operators";
import {statisticsResolverModel} from "@app/models/resolvers/statistics-resolver-model";

@Injectable({
  providedIn: "root"
})
export class StatisticsResolver {
  dataModel: statisticsResolverModel;

  constructor(private httpService: HttpService, private authenticationService: AuthenticationService) {
  }

  resolve(): Observable<boolean> {
    if (this.authenticationService.session.role === "analyst") {
      return this.httpService.requestStatisticsResource().pipe(
        map((response) => {
          this.dataModel = response;
          return true;
        })
      );
    }
    return of(true);
  }
}
