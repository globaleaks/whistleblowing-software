import {Component, Input} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import {HttpService} from "@app/shared/services/http.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {UtilsService} from "@app/shared/services/utils.service";
import {AppConfigService} from "@app/services/app-config.service";

@Component({
  selector: "src-substatusmanager",
  templateUrl: "./sub-status-manager.component.html"
})
export class SubStatusManagerComponent {
  editing = false;
  @Input() submissionsStatus: any;
  @Input() submissionStatuses: any;
  @Input() index: number;
  @Input() first: boolean;
  @Input() last: boolean;


  constructor(private appConfigService: AppConfigService, private appDataServices: AppDataService, private httpService: HttpService, private modalService: NgbModal, private utilsService: UtilsService) {

  }

  isSystemDefined(state: any): boolean {
    return ["new", "opened", "closed"].indexOf(state.id) !== -1;
  }

  toggleEditing(submissionsStatus: any): void {
    if (this.isEditable(submissionsStatus)) {
      this.editing = !this.editing;
    }
  }

  isEditable(submissionsStatus: any): boolean {
    return ["new", "opened"].indexOf(submissionsStatus.id) === -1;
  }

  moveUp(e: any, idx: number): void {
    this.swap(e, idx, -1);
  }

  moveDown(e: any, idx: number): void {
    this.swap(e, idx, 1);
  }

  ssIdx(ssID: any): number | undefined {
    for (let i = 0; i < this.appDataServices.submissionStatuses.length; i++) {
      const status = this.appDataServices.submissionStatuses[i];
      if (status.id === ssID) {
        return i;
      }
    }
    return undefined;
  }

  swap($event: any, index: number, n: number): void {
    $event.stopPropagation();

    const target = index + n;

    if (target < 0 || target >= this.appDataServices.submissionStatuses.length) {
      return;
    }

    const origIndex = this.ssIdx(this.appDataServices.submissionStatuses[index].id);
    const origTarget = this.ssIdx(this.appDataServices.submissionStatuses[target].id);

    if (origIndex !== undefined && origTarget !== undefined) {
      const movingStatus = this.appDataServices.submissionStatuses[origIndex];
      this.appDataServices.submissionStatuses[origIndex] = this.appDataServices.submissionStatuses[origTarget];
      this.appDataServices.submissionStatuses[origTarget] = movingStatus;

      const reorderedIds = {
        ids: this.appDataServices.submissionStatuses
          .map((c: any) => c.id)
          .filter((c: number | string) => c)
      };
      const data = {
        "operation": "order_elements",
        "args": reorderedIds,
      };
      this.httpService.runOperation("api/admin/statuses", "order_elements", data, false);
    }
  }

  deleteSubmissionStatus(submissionsStatus: any): void {
    this.utilsService.openConfirmableModalDialog(submissionsStatus, "").subscribe();
  }

  saveSubmissionsStatus(submissionsStatus: any): void {
    const url = "api/admin/statuses/" + submissionsStatus.id;
    this.httpService.requestUpdateStatus(url, submissionsStatus).subscribe(_ => {
      this.utilsService.deleteResource(this.submissionStatuses,submissionsStatus);
    });
  }
}
