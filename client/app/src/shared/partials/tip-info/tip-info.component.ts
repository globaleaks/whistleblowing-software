import {Component, Input} from "@angular/core";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {WbtipService} from "@app/services/helper/wbtip.service";
import {AppDataService} from "@app/app-data.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {ReceiverTipService} from "@app/services/helper/receiver-tip.service";
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

  markReportStatus(date: string) {
    const report_date = new Date(date);
    const current_date = new Date();
    return current_date > report_date;
  };

  updateLabel(label: string) {
    this.httpService.tipOperation("set", {"key": "label", "value": label}, this.rTipService.tip.id).subscribe(() => {
    });
  }
}
