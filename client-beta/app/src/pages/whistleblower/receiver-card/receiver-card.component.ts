import {Component, Input} from "@angular/core";
import {TranslateService} from "@ngx-translate/core";

@Component({
  selector: "src-receiver-card",
  templateUrl: "./receiver-card.component.html"
})
export class ReceiverCardComponent {
  @Input() submission: any;
  @Input() receiver: any;

  constructor(protected translate: TranslateService) {
  }

}
