import {Component, Input, OnInit} from "@angular/core";
import {DeleteConfirmationComponent} from "@app/shared/modals/delete-confirmation/delete-confirmation.component";
import {UtilsService} from "@app/shared/services/utils.service";
import {HttpClient} from "@angular/common/http";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {AppConfigService} from "@app/services/app-config.service";
import {HttpService} from "@app/shared/services/http.service";
import {Observable} from "rxjs";

@Component({
  selector: "src-substatuses",
  templateUrl: "./sub-status.component.html"
})
export class SubStatusComponent implements OnInit {
  @Input() submissionsStatus: any;
  subStatusEditing: boolean[] = [];
  newSubStatus: any;
  showAddSubStatus: boolean = false;

  toggleAddSubStatus(): void {
    this.showAddSubStatus = !this.showAddSubStatus;
  }

  constructor(private httpService: HttpService, private appConfigService: AppConfigService, protected modalService: NgbModal, protected utilsService: UtilsService, private http: HttpClient) {
  }

  ngOnInit(): void {
    this.subStatusEditing = new Array(this.submissionsStatus.length).fill(false);
  }

  addSubmissionSubStatus(): void {
    const order = this.utilsService.newItemOrder(this.submissionsStatus.substatuses, "order");
    const newSubmissionsSubStatus = {
      label: this.newSubStatus,
      order: order
    };

    this.http.post<any>(
      `/api/admin/statuses/${this.submissionsStatus.id}/substatuses`,
      newSubmissionsSubStatus
    ).subscribe(
      result => {
        this.submissionsStatus.substatuses.push(result);
        this.newSubStatus = "";
      }
    );
  }

  swapSs($event: any, index: number, n: number): void {
    $event.stopPropagation();

    const target = index + n;

    if (target < 0 || target >= this.submissionsStatus.substatuses.length) {
      return;
    }

    const temp = this.submissionsStatus.substatuses[index];
    this.submissionsStatus.substatuses[index] = this.submissionsStatus.substatuses[target];
    this.submissionsStatus.substatuses[target] = temp;

    const ids = this.submissionsStatus.substatuses.map((c: any) => c.id);

    this.http.put<any>(
      `/api/admin/statuses/${this.submissionsStatus.id}/substatuses`,
      {
        operation: "order_elements",
        args: {ids: ids}
      }
    ).subscribe();
  }

  saveSubmissionsSubStatus(subStatusParam: any): void {
    const url = "api/admin/statuses/" + this.submissionsStatus.id + "/substatuses/" + subStatusParam.id;
    this.httpService.requestUpdateStatus(url, subStatusParam).subscribe(_ => {
      this.appConfigService.reinit();
    });
  }

  deleteSubSubmissionStatus(subStatusParam: any): void {
    this.openConfirmableModalDialog(subStatusParam, "").subscribe();
  }

  openConfirmableModalDialog(arg: any, scope: any): Observable<string> {
    scope = !scope ? this : scope;
    return new Observable((observer) => {
      let modalRef = this.modalService.open(DeleteConfirmationComponent, {});
      modalRef.componentInstance.arg = arg;
      modalRef.componentInstance.scope = scope;
      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
        const url = "api/admin/statuses/" + this.submissionsStatus.id + "/substatuses/" + arg.id;
        return this.utilsService.deleteSubStatus(url).subscribe(_ => {
          this.appConfigService.reinit();
        });
      };
    });
  }

  moveSsUp(e: any, idx: number): void {
    this.swapSs(e, idx, -1);
  }

  moveSsDown(e: any, idx: number): void {
    this.swapSs(e, idx, 1);
  }

  toggleSubstatusEditing(index: number): void {
    this.subStatusEditing[index] = !this.subStatusEditing[index];
  }
}
