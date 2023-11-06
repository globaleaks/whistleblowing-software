import {Component, EventEmitter, Input, Output} from "@angular/core";
import * as Constants from "@app/shared/constants/constants";
import {AppDataService} from "@app/app-data.service";

@Component({
  selector: "src-wbpa",
  templateUrl: "./wbpa.component.html"
})
export class WbpaComponent {
  @Input() signup: any;
  @Output() complete: EventEmitter<any> = new EventEmitter<any>();
  @Output() updateSubdomain: EventEmitter<any> = new EventEmitter<any>();

  protected readonly Constants = Constants;
  validated = false;
  confirmation_email: any;
  domainPattern: string = "^[a-z0-9]+$";

  constructor(protected appDataService: AppDataService) {
  }
}
