import {Injectable} from "@angular/core";
import {Observable, of} from "rxjs";
import {HttpService} from "@app/shared/services/http.service";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {notificationResolverModel} from "@app/models/resolvers/notification-resolver-model";
import {map} from "rxjs/operators";

@Injectable({
  providedIn: "root"
})
export class NotificationsResolver  {
  dataModel: notificationResolverModel = new notificationResolverModel();

  constructor(private httpService: HttpService, private authenticationService: AuthenticationService) {
  }

  resolve(): Observable<boolean> {
    if (this.authenticationService.session.role === "admin") {
      return this.httpService.requestNotificationsResource().pipe(
        map((response: notificationResolverModel) => {
          this.dataModel = response;
          return true;
        })
      );
    }
    return of(true);
  }
}
