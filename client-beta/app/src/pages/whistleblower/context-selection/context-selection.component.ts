import {Component, EventEmitter, Input, Output} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-context-selection",
  templateUrl: "./context-selection.component.html"
})
export class ContextSelectionComponent {

  @Input() selectable_contexts: any;
  @Input() contextsOrderPredicate: any;
  @Output() selectContext: EventEmitter<any> = new EventEmitter();

  constructor(protected appDataService: AppDataService, protected utilsService: UtilsService) {
  }
}
