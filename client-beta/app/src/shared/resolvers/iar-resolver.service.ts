import {Injectable} from "@angular/core";

import {Observable, of} from "rxjs";
import {map} from "rxjs/operators";
import {HttpService} from "@app/shared/services/http.service";
import {AuthenticationService} from "@app/services/authentication.service";
import {IarData} from "@app/models/reciever/Iar-data";

@Injectable({
  providedIn: "root"
})
export class IarResolver  {
  dataModel: IarData[] = [];

  constructor(
    private httpService: HttpService,
    private authenticationService: AuthenticationService
  ) {
  }

  resolve(): Observable<boolean> {
    if (this.authenticationService.session.role === "custodian") {
      return this.httpService.iarResource().pipe(
        map((response: IarData[]) => {
          this.dataModel = response;
          return true;
        })
      );
    }
    return of(true);
  }
}
