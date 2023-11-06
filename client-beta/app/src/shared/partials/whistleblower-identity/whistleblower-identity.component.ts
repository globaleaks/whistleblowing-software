import {Component, EventEmitter, Input, Output} from "@angular/core";
import {WbtipService} from "@app/services/wbtip.service";
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
  @Input() answers: any;
  @Output() provideIdentityInformation = new EventEmitter<{ param1: any, param2: any }>();
  @Output() onFormUpdate = new EventEmitter<void>();
  @Output() notifyFileUpload: EventEmitter<any> = new EventEmitter<any>();

  @Input() uploadEstimateTime: any;
  @Input() isUploading: any;
  @Input() uploadProgress: any;
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
