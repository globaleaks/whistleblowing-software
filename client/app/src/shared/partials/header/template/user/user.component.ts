import {ChangeDetectorRef, Component} from "@angular/core";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {AppConfigService} from "@app/services/root/app-config.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {AppDataService} from "@app/app-data.service";
import {TranslationService} from "@app/services/helper/translation.service";
import {HttpService} from "@app/shared/services/http.service";
import {ActivatedRoute} from "@angular/router";

@Component({
  selector: "views-user",
  templateUrl: "./user.component.html"
})
export class UserComponent {

  constructor(protected activatedRoute: ActivatedRoute, protected httpService: HttpService, protected appConfigService: AppConfigService, private cdr: ChangeDetectorRef, protected authentication: AuthenticationService, protected preferences: PreferenceResolver, protected utils: UtilsService, protected appDataService: AppDataService, protected translationService: TranslationService) {
    this.onQueryParameterChangeListener();
  }

  onQueryParameterChangeListener() {
    this.activatedRoute.queryParams.subscribe(params => {
      const storageLanguage = localStorage.getItem("default_language");
      if (params["lang"]) {
        const paramLangValue = params["lang"] && this.appDataService.public.node.languages_enabled.includes(params["lang"]) ? params["lang"] : "";
        if (paramLangValue) {
          if (storageLanguage !== paramLangValue) {
            this.translationService.onChange(paramLangValue);
            this.appConfigService.reinit(false);
            this.utils.reloadCurrentRouteFresh();
          }
          localStorage.setItem("default_language", paramLangValue);
        }
      }
    });
  }

  onLogout(event: Event) {
    event.preventDefault();
    const promise = () => {
      localStorage.removeItem("default_language");
      this.translationService.onChange(this.appDataService.public.node.default_language);
      this.appConfigService.reinit(false);
      this.appConfigService.onValidateInitialConfiguration();
    };

    this.authentication.logout(promise);
  }

  getHomepage() {
    return this.authentication.session.homepage;
  }

  getPreferencepage() {
    return this.authentication.session.preferencespage;
  }

  onChangeLanguage() {
    this.cdr.detectChanges();
    localStorage.removeItem("default_language");
    this.translationService.onChange(this.translationService.language);
    this.appConfigService.reinit(false);
    this.utils.reloadCurrentRouteFresh(true);
  }
}
