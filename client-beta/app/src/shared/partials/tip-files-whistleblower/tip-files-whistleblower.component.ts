import {Component, Input} from "@angular/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {WbtipService} from "@app/services/wbtip.service";

@Component({
  selector: "src-tip-files-whistleblower",
  templateUrl: "./tip-files-whistleblower.component.html"
})
export class TipFilesWhistleblowerComponent {
  @Input() fileUploadUrl: any;
  collapsed = false;

  constructor(protected utilsService: UtilsService, protected wbTipService: WbtipService) {
  }

  public toggleColLapse() {
    this.collapsed = !this.collapsed;
  }
}
