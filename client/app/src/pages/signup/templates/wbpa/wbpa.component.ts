import {Component, EventEmitter, Input, Output} from "@angular/core";
import * as Constants from "@app/shared/constants/constants";
import {AppDataService} from "@app/app-data.service";
import {Signup} from "@app/models/component-model/signup";

@Component({
  selector: "src-wbpa",
  templateUrl: "./wbpa.component.html"
})
export class WbpaComponent {
  @Input() signup: Signup;
  @Output() complete: EventEmitter<any> = new EventEmitter<any>();
  @Output() updateSubdomain: EventEmitter<any> = new EventEmitter<any>();

  protected readonly Constants = Constants;
  validated = false;
  confirmation_email: string;
  domainPattern: string = "^[a-z0-9-]+$";

  constructor(protected appDataService: AppDataService) {
  }
}
