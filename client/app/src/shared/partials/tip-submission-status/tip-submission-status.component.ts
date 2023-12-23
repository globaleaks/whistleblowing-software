import {Component, Input, OnInit} from "@angular/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {WbtipService} from "@app/services/helper/wbtip.service";
import {AppDataService} from "@app/app-data.service";
import {ReceiverTipService} from "@app/services/helper/receiver-tip.service";
import {HttpService} from "@app/shared/services/http.service";

@Component({
  selector: "src-tip-submission-status",
  templateUrl: "./tip-submission-status.component.html"
})
export class TipSubmissionStatusComponent implements OnInit{
  @Input() tipService: ReceiverTipService | WbtipService;
  @Input() loading: boolean;
  tipStatus = ""
  tipSubStatus = ""


  constructor(protected httpService: HttpService, protected utilsService: UtilsService, protected appDataService: AppDataService) {
  }

  public ngOnInit(): void {

    if(!this.loading){
      if(this.appDataService.submission_statuses_by_id[this.tipService.tip.status.toLowerCase()]){
        this.tipStatus = this.tipService.tip.status;
      }

      if(this.appDataService.submission_statuses_by_id[this.tipService.tip.status.toLowerCase()] && this.appDataService.submission_statuses_by_id[this.tipService.tip.status.toLowerCase()].substatuses.find((item: { id: string; }) => item.id === this.tipService.tip.substatus)){
        this.tipSubStatus = this.tipService.tip.substatus;
      }
    }else {
      this.tipStatus = "";
    }

  }

  updateSubmissionStatus() {
    this.tipService.tip.substatus = "";
    this.tipService.tip.status = this.tipStatus;
    const args = {"status": this.tipStatus, "substatus": ""};
    this.httpService.tipOperation("update_status", args, this.tipService.tip.id)
      .subscribe(
        () => {
          this.utilsService.reloadComponent();
        }
      );
  };

  updateSubmissionSubStatus() {
    this.tipService.tip.substatus = this.tipSubStatus;
    const args = {
      "status": this.tipStatus,
      "substatus": this.tipSubStatus ? this.tipSubStatus : ""
    };
    this.httpService.tipOperation("update_status", args, this.tipService.tip.id)
      .subscribe(
        () => {
          this.utilsService.reloadComponent();
        }
      );
  };
}
