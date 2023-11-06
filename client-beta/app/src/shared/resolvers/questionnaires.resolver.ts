import {Injectable} from "@angular/core";

import {Observable, of} from "rxjs";
import {HttpService} from "@app/shared/services/http.service";
import {AuthenticationService} from "@app/services/authentication.service";
import {questionnaireResolverModel} from "@app/models/resolvers/questionnaire-model";
import {map} from "rxjs/operators";

@Injectable({
  providedIn: "root"
})
export class QuestionnairesResolver  {
  dataModel: any = new questionnaireResolverModel();

  constructor(private httpService: HttpService, private authenticationService: AuthenticationService) {
  }

  resolve(): Observable<boolean> {
    if (this.authenticationService.session.role === "admin") {
      return this.httpService.requestQuestionnairesResource().pipe(
        map((response: questionnaireResolverModel) => {
          this.dataModel = response;
          return true;
        })
      );
    }
    return of(true);
  }
}
