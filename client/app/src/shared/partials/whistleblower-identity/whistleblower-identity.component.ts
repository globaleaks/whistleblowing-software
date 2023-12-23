import {Component, EventEmitter, Input, Output} from "@angular/core";
import {Answers} from "@app/models/reciever/reciever-tip-data";
import {WbtipService} from "@app/services/helper/wbtip.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-whistleblower-identity",
  templateUrl: "./whistleblower-identity.component.html"
})
export class WhistleblowerIdentityComponent {
  collapsed = false;
  protected readonly JSON = JSON;
  @Input() field: any;
  @Input() step: any;
  @Input() answers: Answers;
  @Output() provideIdentityInformation = new EventEmitter<{ param1: string, param2: Answers }>();
  @Output() onFormUpdate = new EventEmitter<void>();
  @Output() notifyFileUpload: EventEmitter<any> = new EventEmitter<any>();

  @Input() uploadEstimateTime: number;
  @Input() isUploading:boolean|undefined;
  @Input() uploadProgress: number|undefined;
  identity_provided: boolean = true;

  constructor(protected wbTipService: WbtipService, protected utilsService: UtilsService) {
    this.collapsed = this.wbTipService.tip.data.whistleblower_identity_provided;
  }

  public toggleCollapse() {
    this.collapsed = !this.collapsed;
  }

  onFormChange() {
    this.onFormUpdate.emit();
  }

  stateChanged(status: boolean) {
    this.identity_provided = status;
  }
}
