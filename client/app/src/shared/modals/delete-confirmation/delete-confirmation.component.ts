import {HttpClient} from "@angular/common/http";
import {Component, Input} from "@angular/core";
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";
import {UtilsService} from "@app/shared/services/utils.service";
import {Router} from "@angular/router";


@Component({
  selector: "src-delete-confirmation",
  templateUrl: "./delete-confirmation.component.html"
})
export class DeleteConfirmationComponent {

  @Input() args: any;
  @Input() selected_tips: string[];
  @Input() operation: string;
  confirmFunction: () => void;

  constructor(private modalService: NgbActiveModal, private http: HttpClient, private utils: UtilsService, private router: Router) {
  }

  confirm() {
    this.cancel();
    this.confirmFunction();
    if (this.args) {
      if (this.args.operation === "delete") {
        return this.http.delete("api/recipient/rtips/" + this.args.tip.id)
          .subscribe(() => {
            this.router.navigate(["/recipient/reports"]).then();
          });
      }
      return;
    }
    if (this.operation) {
      if (["delete"].indexOf(this.operation) === -1) {
        return;
      }
    }

    if (this.selected_tips) {
      return this.utils.runRecipientOperation(this.operation, {"rtips": this.selected_tips}, true).subscribe({
        next: _ => {
          this.utils.reloadCurrentRoute();
        }
      });
    } else {
      return null;
    }

  }

  cancel() {
    this.modalService.dismiss();
  }

}
