import {Component, OnInit} from "@angular/core";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {UtilsService} from "@app/shared/services/utils.service";
import {AppDataService} from "@app/app-data.service";
import {HttpService} from "@app/shared/services/http.service";
import {Router} from "@angular/router";
import {ErrorCodes} from "@app/models/app/error-code";
import {CryptoService} from "@app/shared/services/crypto.service";

@Component({
  selector: "src-password-change",
  templateUrl: "./password-change.component.html"
})
export class PasswordChangeComponent implements OnInit {
  passwordStrengthScore: number = 0;

  changePasswordArgs = {
    current: "",
    password: "",
    confirm: "",
    old_hash: "",
    hash : ""
  };

  async changePassword() {
    this.changePasswordArgs.hash = await this.cryptoService.hashArgon2(this.changePasswordArgs.password, this.preferencesService.dataModel.username)
    this.changePasswordArgs.old_hash = this.preferencesService.dataModel.password_change_needed == false ? await this.cryptoService.hashArgon2(this.changePasswordArgs.current, this.preferencesService.dataModel.username) : "";
    const data = {
      "operation": "change_password",
      "args": this.changePasswordArgs
    };
    const requestObservable = this.httpService.requestOperations(data);
    requestObservable.subscribe(
      {
        next: _ => {
          this.preferencesService.dataModel.password_change_needed = false;
          this.router.navigate([this.authenticationService.session.homepage]).then();
        },
        error: (error) => {
          this.passwordStrengthScore = 0;
          this.rootDataService.errorCodes = new ErrorCodes(error.error["error_message"], error.error["error_code"], error.error.arguments);
          this.appDataService.updateShowLoadingPanel(false);
          return this.passwordStrengthScore;
        }
      }
    );
  }

  ngOnInit() {
  };

  onPasswordStrengthChange(score: number) {
    this.passwordStrengthScore = score;
  }

  public constructor(private cryptoService: CryptoService, public rootDataService: AppDataService, private authenticationService: AuthenticationService, private router: Router, public httpService: HttpService, public appDataService: AppDataService, public authentication: AuthenticationService, public preferencesService: PreferenceResolver, public utilsService: UtilsService) {

  }

}
