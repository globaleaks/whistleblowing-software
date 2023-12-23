import {Component} from "@angular/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {FormBuilder, FormGroup} from "@angular/forms";
import {TwoFactorAuthData} from "@app/services/helper/2fa.data.service";

@Component({
  selector: "src-enable-2fa",
  templateUrl: "./enable-2fa.html"
})
export class Enable2fa {

  symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
  array = new Uint32Array(32);
  OTPSecretForm: FormGroup;

  constructor(protected utils: UtilsService, protected preferenceResolver: PreferenceResolver, private builder: FormBuilder, protected twoFactorAuthData: TwoFactorAuthData) {
    this.initialization();
  }

  ngOnInit() {
    this.OTPSecretForm = this.builder.group({});
  };

  initialization() {
    window.crypto.getRandomValues(this.array);

    for (let i = 0; i < this.array.length; i++) {
      this.twoFactorAuthData.totp.secret += this.symbols[this.array[i] % this.symbols.length];
    }

    this.onSecretKeyChanged();
  }

  onSecretKeyChanged() {
    this.twoFactorAuthData.totp.qrcode_string = "otpauth://totp/" + location.host + "%20%28" + this.preferenceResolver.dataModel.username + "%29?secret=" + this.twoFactorAuthData.totp.secret;
  }
}
