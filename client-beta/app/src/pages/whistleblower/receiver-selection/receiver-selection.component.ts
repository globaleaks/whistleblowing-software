import {Component, EventEmitter, Input, Output} from "@angular/core";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-receiver-selection",
  templateUrl: "./receiver-selection.component.html"
})
export class ReceiverSelectionComponent {

  @Input() show_steps_navigation_bar: boolean;
  @Input() submission: any;
  @Input() receiversOrderPredicate: any;
  @Output() switchSelection: EventEmitter<any> = new EventEmitter();

  constructor(protected utilsService: UtilsService) {
  }

}
