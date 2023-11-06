import {Component, Input} from "@angular/core";
import {AuthenticationService} from "@app/services/authentication.service";
import {LoginDataRef} from "@app/pages/auth/login/model/login-model";
import {UtilsService} from "@app/shared/services/utils.service";
import {ControlContainer, NgForm} from "@angular/forms";

@Component({
  selector: "app-default-login",
  templateUrl: "./default-login.component.html",
  viewProviders: [{provide: ControlContainer, useExisting: NgForm}],
})
export class DefaultLoginComponent {

  @Input() loginData: LoginDataRef;
  @Input() loginValidator: NgForm;
  loginAuthCode: any;

  constructor(protected utils: UtilsService, protected authentication: AuthenticationService) {
  }
}
