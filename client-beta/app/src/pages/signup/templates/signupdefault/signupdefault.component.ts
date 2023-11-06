import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import * as Constants from "@app/shared/constants/constants";

@Component({
  selector: "src-signupdefault",
  templateUrl: "./signupdefault.component.html"
})
export class SignupdefaultComponent implements OnInit {

  @Input() signup: any;
  @Output() complete: EventEmitter<any> = new EventEmitter<any>();

  emailRegex: any;
  confirmation_email: any;
  validated = false;
  domainPattern: string = "^[a-z0-9]+$";
  mail: any;

  constructor(protected appDataService: AppDataService) {
  }

  ngOnInit(): void {
    this.emailRegex = Constants.Constants.emailRegexp;
  }
}
