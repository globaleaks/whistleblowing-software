import {HttpClient} from "@angular/common/http";
import {Component, OnInit} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import {preferenceResolverModel} from "@app/models/resolvers/preference-resolver-model";
import {AcceptAgreementComponent} from "@app/shared/modals/accept-agreement/accept-agreement.component";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {Observable} from "rxjs";

@Component({
  selector: "src-custodian-home",
  templateUrl: "./home.component.html"
})
export class HomeComponent implements OnInit {
  preferenceData: preferenceResolverModel;

  constructor(private appDataService: AppDataService, private http: HttpClient, private modalService: NgbModal, private preference: PreferenceResolver) {
  }

  ngOnInit(): void {
    if (this.preference.dataModel) {
      this.preferenceData = this.preference.dataModel;
    }
    if (this.appDataService.public.node.user_privacy_policy_text && this.preferenceData.accepted_privacy_policy === "1970-01-01T00:00:00Z") {
      this.acceptPrivacyPolicyDialog().subscribe();
    }
  }

  acceptPrivacyPolicyDialog(): Observable<string> {
    return new Observable((observer) => {
      let modalRef = this.modalService.open(AcceptAgreementComponent, {
        backdrop: 'static',
        keyboard: false,
      });
      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
        return this.http.put("api/user/operations", {
          operation: "accepted_privacy_policy",
          args: {}
        }).subscribe(() => {
          this.preferenceData.accepted_privacy_policy = "";
          modalRef.close();
        });
      };
    });
  }
}
