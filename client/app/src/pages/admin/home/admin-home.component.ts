import {HttpClient} from "@angular/common/http";
import {Component, OnInit} from "@angular/core";
import {Router} from "@angular/router";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {AcceptAgreementComponent} from "@app/shared/modals/accept-agreement/accept-agreement.component";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {Observable} from "rxjs";
import {nodeResolverModel} from "@app/models/resolvers/node-resolver-model";
import {preferenceResolverModel} from "@app/models/resolvers/preference-resolver-model";

@Component({
  selector: "src-admin-home",
  templateUrl: "./admin-home.component.html"
})
export class adminHomeComponent implements OnInit {
  active: number = 0;
  nodeData: nodeResolverModel;
  preferenceData: preferenceResolverModel;

  constructor(private http: HttpClient, private modalService: NgbModal, private preference: PreferenceResolver, protected nodeResolver: NodeResolver, private router: Router) {
  }

  ngOnInit(): void {
    if (this.nodeResolver.dataModel) {
      this.nodeData = this.nodeResolver.dataModel;
    }
    if (this.preference.dataModel) {
      this.preferenceData = this.preference.dataModel;
    }
    if (this.nodeData.user_privacy_policy_text && this.preferenceData.accepted_privacy_policy === "1970-01-01T00:00:00Z") {
      this.acceptPrivacyPolicyDialog().subscribe();
    }
  }

  acceptPrivacyPolicyDialog(): Observable<string> {
    return new Observable((observer) => {
      let modalRef = this.modalService.open(AcceptAgreementComponent, {backdrop: 'static', keyboard: false});
      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
        return this.http.put("api/user/operations", {
          operation: "accepted_privacy_policy",
          args: {}
        }).subscribe(() => {
          this.preferenceData.accepted_privacy_policy = "";
        });
      };
    });
  }

  isActive(route: string): boolean {
    return this.router.isActive(route, {
      paths: "subset",
      queryParams: "subset",
      fragment: "ignored",
      matrixParams: "ignored"
    });
  }
}