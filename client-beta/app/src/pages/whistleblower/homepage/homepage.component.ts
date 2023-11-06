import {Component} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import {DeleteConfirmationComponent} from "@app/shared/modals/delete-confirmation/delete-confirmation.component";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {DisclaimerComponent} from "@app/shared/modals/disclaimer/disclaimer.component";
import {Observable} from "rxjs";

@Component({
  selector: "src-homepage",
  templateUrl: "./homepage.component.html"
})
export class HomepageComponent {

  constructor(protected appDataService: AppDataService, private modalService: NgbModal, private nodeResolver: NodeResolver) {
  }

  openSubmission() {
    if (this.nodeResolver.dataModel.disclaimer_text) {
      return this.openDisclaimerModal().subscribe();
    }
    return this.appDataService.page = "submissionpage";
  }

  openDisclaimerModal(): Observable<string> {
    return new Observable((observer) => {
      let modalRef = this.modalService.open(DisclaimerComponent, {});
      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
        modalRef.componentInstance.confirmFunction = () => {
          return this.appDataService.page = "submissionpage";
        };
      };
    });
  }
}
