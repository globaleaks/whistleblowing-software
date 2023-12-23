import {Component} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {DisclaimerComponent} from "@app/shared/modals/disclaimer/disclaimer.component";
import {Observable} from "rxjs";
import {AppConfigService} from "@app/services/root/app-config.service";

@Component({
  selector: "src-homepage",
  templateUrl: "./homepage.component.html"
})
export class HomepageComponent {

  constructor(protected appConfigService: AppConfigService, protected appDataService: AppDataService, private modalService: NgbModal) {
  }

  openSubmission() {
    if (this.appDataService.public.node.disclaimer_text) {
      return this.openDisclaimerModal().subscribe();
    }
    this.appConfigService.setPage("submissionpage");
    return this.appDataService.page;
  }

  openDisclaimerModal(): Observable<string> {
    return new Observable((observer) => {
      let modalRef = this.modalService.open(DisclaimerComponent,{backdrop: 'static',keyboard: false});
      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
        this.appConfigService.setPage("submissionpage");
        return this.appDataService.page;
      };
    });
  }
}
