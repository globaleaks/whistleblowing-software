import {Component, Input} from "@angular/core";
import {AuthenticationService} from "@app/services/authentication.service";
import {WbtipService} from "@app/services/wbtip.service";
import {AppDataService} from "@app/app-data.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {ReceiverTipService} from "@app/services/receiver-tip.service";
import {HttpService} from "@app/shared/services/http.service";

@Component({
  selector: "src-tip-info",
  templateUrl: "./tip-info.component.html"
})
export class TipInfoComponent {
  @Input() tipService: ReceiverTipService | WbtipService;
  @Input() loading: boolean;

  constructor(protected authenticationService: AuthenticationService, protected appDataService: AppDataService, protected utilsService: UtilsService, private rTipService: ReceiverTipService, private httpService: HttpService,) {
  }

  markReportStatus(date: any) {
    const report_date = new Date(date);
    const current_date = new Date();
    return current_date > report_date;
  };

  updateLabel(label: any) {
    this.httpService.tipOperation("set", {"key": "label", "value": label}, this.rTipService.tip.id).subscribe(() => {
    });
  }
}
