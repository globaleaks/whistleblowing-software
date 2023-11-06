import {Injectable} from "@angular/core";
import {CryptoService} from "@app/crypto.service";
import {UtilsService} from "./utils.service";
import {TranslationService} from "@app/services/translation.service";
import {SubmissionService} from "@app/services/submission.service";
import {AuthenticationService} from "@app/services/authentication.service";
import {AppConfigService} from "@app/services/app-config.service";

@Injectable({
  providedIn: "root"
})
export class ServiceInstanceService {

  public utilsService: UtilsService;
  public appConfigService: AppConfigService;
  public authenticationService: AuthenticationService;
  public translationService: TranslationService;
  public submissionService: SubmissionService;
  public cryptoService: CryptoService;

  constructor() {

  }

  setUtilsService(instance: UtilsService): void {
    this.utilsService = instance;
  }

  setAppConfigService(instance: AppConfigService): void {
    this.appConfigService = instance;
  }

  setAuthenticationService(instance: AuthenticationService): void {
    this.authenticationService = instance;
  }

  setTranslationService(instance: TranslationService): void {
    this.translationService = instance;
  }

  setSubmissionService(instance: SubmissionService): void {
    this.submissionService = instance;
  }

  setCryptoService(instance: CryptoService): void {
    this.cryptoService = instance;
  }
}
