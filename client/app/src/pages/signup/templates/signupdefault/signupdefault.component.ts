import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import {Signup} from "@app/models/component-model/signup";
import * as Constants from "@app/shared/constants/constants";

@Component({
  selector: "src-signupdefault",
  templateUrl: "./signupdefault.component.html"
})
export class SignupdefaultComponent implements OnInit {

  @Input() signup: Signup;
  @Output() complete: EventEmitter<any> = new EventEmitter<any>();

  emailRegex: string;
  confirmation_email: string;
  validated = false;
  domainPattern: string = "^[a-z0-9]+$";
  mail: string;

  constructor(protected appDataService: AppDataService) {
  }

  ngOnInit(): void {
    this.emailRegex = Constants.Constants.emailRegexp;
  }
}
