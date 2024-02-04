import {Component} from "@angular/core";
import {TwoFactorAuthData} from "@app/services/helper/2fa.data.service";
import {HttpService} from "@app/shared/services/http.service";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {Router} from "@angular/router";

@Component({
  selector: "src-forced-two-factor",
  templateUrl: "./forced-two-factor.component.html"
})
export class ForcedTwoFactorComponent {
  constructor(protected twoFactorAuthData: TwoFactorAuthData, private httpService: HttpService, private preferenceResolver: PreferenceResolver, private authenticationService: AuthenticationService, private router: Router) {
    this.twoFactorAuthData.totp.secret = ""
    this.twoFactorAuthData.totp.token = ""
  }

  enable2FA() {
    const data = {
      "operation": "enable_2fa",
      "args": {
        "secret": this.twoFactorAuthData.totp.secret,
        "token": this.twoFactorAuthData.totp.token
      }
    };

    const requestObservable = this.httpService.requestOperations(data);
    requestObservable.subscribe(
      {
        next: () => {
          this.preferenceResolver.dataModel.two_factor = true;
          this.authenticationService.session.two_factor = true;
          this.router.navigate([this.authenticationService.session.homepage]).then();
        }
      }
    );
  }
}