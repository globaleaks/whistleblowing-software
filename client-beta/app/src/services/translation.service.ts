import {Injectable} from "@angular/core";
import {TranslateService} from "@ngx-translate/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {AppConfigService} from "@app/services/app-config.service";
import {ServiceInstanceService} from "@app/shared/services/service-instance.service";

@Injectable({
  providedIn: "root",
})
export class TranslationService {

  language = "";

  public utilsService: UtilsService;
  public appConfigService: AppConfigService;

  constructor(private serviceInstanceService: ServiceInstanceService, private translateService: TranslateService) {
  }

  init() {
    this.utilsService = this.serviceInstanceService.utilsService;
    this.appConfigService = this.serviceInstanceService.appConfigService;
  }

  onChange(changedLanguage: string) {
    this.language = changedLanguage;
    this.translateService.use(this.language).subscribe(() => {
      this.translateService.setDefaultLang(this.language);
      this.translateService.getTranslation(this.language).subscribe();
    });
  }
}
