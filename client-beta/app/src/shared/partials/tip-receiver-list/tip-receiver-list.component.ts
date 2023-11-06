import {Component, Input} from "@angular/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {WbtipService} from "@app/services/wbtip.service";
import {ReceiverTipService} from "@app/services/receiver-tip.service";

@Component({
  selector: "src-tip-receiver-list",
  templateUrl: "./tip-receiver-list.component.html"
})
export class TipReceiverListComponent {
  collapsed = false;
  @Input() tipService: ReceiverTipService | WbtipService;

  constructor(protected utilsService: UtilsService) {
  }

  public toggleCollapse() {
    this.collapsed = !this.collapsed;
  }

}
