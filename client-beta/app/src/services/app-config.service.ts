import {Injectable} from "@angular/core";
import {HttpService} from "@app/shared/services/http.service";
import {TranslateService} from "@ngx-translate/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {AppDataService} from "@app/app-data.service";
import {FieldUtilitiesService} from "@app/shared/services/field-utilities.service";
import {TranslationService} from "@app/services/translation.service";
import {Router, NavigationEnd, ActivatedRoute, NavigationStart, NavigationError} from "@angular/router";
import {AuthenticationService} from "@app/services/authentication.service";
import {ServiceInstanceService} from "@app/shared/services/service-instance.service";

@Injectable({
  providedIn: "root"
})
export class AppConfigService {
  public sidebar: string = "";
  public header_title: string = "";

  private translationService: TranslationService;
  public authenticationService: AuthenticationService;
  public utilsService: UtilsService;

  constructor(private serviceInstanceService: ServiceInstanceService, private router: Router, private activatedRoute: ActivatedRoute, private appServices: HttpService, private translateService: TranslateService, private appDataService: AppDataService, private fieldUtilitiesService: FieldUtilitiesService) {
  }

  init() {
    this.translationService = this.serviceInstanceService.translationService;
    this.authenticationService = this.serviceInstanceService.authenticationService;
    this.utilsService = this.serviceInstanceService.utilsService;

    this.activatedRoute.paramMap.subscribe(_ => {
      const currentURL = window.location.hash.substring(2).split("?")[0];
      this.initRoutes(currentURL);
      this.localInitialization();
    });
  }

  initRoutes(currentURL: string) {
    if (this.authenticationService && this.authenticationService.session && currentURL !== "login") {
      const queryParams = this.activatedRoute.snapshot.queryParams;
      const param = localStorage.getItem("default_language");
      if (param) {
        queryParams["lang"] = param;
      }

      if (this.authenticationService.session.role === "admin") {
        this.router.navigate(["/" + this.authenticationService.session.role], {queryParams}).then();
      } else if (this.authenticationService.session.role === "receiver") {
        this.router.navigate(["/recipient"], {queryParams}).then();
      } else if (this.authenticationService.session.role === "custodian") {
        this.router.navigate(["/custodian"], {queryParams}).then();
      }
    } else {
      localStorage.removeItem("default_language");
    }
  }

  public setHomepage() {
    location.replace("/");
  };

  public localInitialization(languageInit = true, callback?: () => void) {
    this.appServices.getPublicResource().subscribe({
      next: data => {
        this.appDataService.public = data.body;
        let elem;
        if (window.location.pathname === "/") {
          if (this.appDataService.public.node.css) {
            elem = document.getElementById("load-custom-css");
            if (elem === null) {
              elem = document.createElement("link");
              elem.setAttribute("id", "load-custom-css");
              elem.setAttribute("rel", "stylesheet");
              elem.setAttribute("type", "text/css");
              elem.setAttribute("href", "s/css");
              document.getElementsByTagName("head")[0].appendChild(elem);
            }
          }

          if (this.appDataService.public.node.script) {
            elem = document.getElementById("load-custom-script");
            if (elem === null) {
              elem = document.createElement("script");
              elem.setAttribute("id", "load-custom-script");
              elem.setAttribute("src", "s/script");
              document.getElementsByTagName("body")[0].appendChild(elem);
            }
          }

          if (this.appDataService.public.node.favicon) {
            const element = window.document.getElementById("favicon");
            if (element !== null) {
              element.setAttribute("href", "s/favicon");
            }
          }
        }

        this.appDataService.contexts_by_id = this.utilsService.array_to_map(this.appDataService.public.contexts);
        this.appDataService.receivers_by_id = this.utilsService.array_to_map(this.appDataService.public.receivers);
        this.appDataService.questionnaires_by_id = this.utilsService.array_to_map(this.appDataService.public.questionnaires);
        this.appDataService.submissionStatuses = this.appDataService.public.submission_statuses;
        this.appDataService.submission_statuses_by_id = this.utilsService.array_to_map(this.appDataService.public.submission_statuses);

        for (const [key] of Object.entries(this.appDataService.questionnaires_by_id)) {
          this.fieldUtilitiesService.parseQuestionnaire(this.appDataService.questionnaires_by_id[key], {});
          this.appDataService.questionnaires_by_id[key].steps = this.appDataService.questionnaires_by_id[key].steps.sort((a: any, b: any) => a.order > b.order);
        }

        for (const [key] of Object.entries(this.appDataService.contexts_by_id)) {
          this.appDataService.contexts_by_id[key].questionnaire = this.appDataService.questionnaires_by_id[this.appDataService.contexts_by_id[key].questionnaire_id];
          if (this.appDataService.contexts_by_id[key].additional_questionnaire_id) {
            this.appDataService.contexts_by_id[key].additional_questionnaire = this.appDataService.questionnaires_by_id[this.appDataService.contexts_by_id[key].additional_questionnaire_id];
          }
        }

        this.appDataService.connection = {
          "tor": data.headers["X-Check-Tor"] === "true" || location.host.match(/\.onion$/),
        };

        this.appDataService.privacy_badge_open = !this.appDataService.connection.tor;
        this.appDataService.languages_enabled = new Map<number, string>();
        this.appDataService.languages_enabled_selector = [];
        this.appDataService.languages_supported = new Map<number, string>();

        const self = this;
        this.appDataService.public.node.languages_supported.forEach(function (lang: any) {
          self.appDataService.languages_supported.set(lang.code, lang);

          if (self.appDataService.public.node.languages_enabled.includes(lang.code)) {
            self.appDataService.languages_enabled.set(lang.code, lang);
            self.appDataService.languages_enabled_selector.push(lang);
          }
        });

        let storageLanguage = localStorage.getItem("default_language");
        if (languageInit) {
          if (!storageLanguage) {
            storageLanguage = self.appDataService.public.node.default_language;
            localStorage.setItem("default_language", storageLanguage);
          }
          this.translationService.onChange(storageLanguage);
        }


        this.setTitle();
        this.appDataService.started = true;
        this.onValidateInitialConfiguration();
        if (callback) {
          callback();
        }
      }
    });
  }

  setTitle() {
    const {public: rootData} = this.appDataService;

    if (!rootData || !rootData.node) {
      return;
    }

    const projectTitle = rootData.node.name;
    let pageTitle = rootData.node.header_title_homepage;


    if (this.header_title && this.router.url !== "/") {
      pageTitle = this.header_title;
    } else if (this.appDataService.page === "receiptpage") {
      pageTitle = "Your report was successful.";
    }

    if (pageTitle && pageTitle.length > 0) {
      pageTitle = this.translateService.instant(pageTitle);
    }

    this.appDataService.projectTitle = projectTitle !== "GLOBALEAKS" ? projectTitle : "";
    this.appDataService.pageTitle = pageTitle !== projectTitle ? pageTitle : "";

    if (pageTitle) {
      const finalPageTitle = pageTitle.length > 0 ? this.translateService.instant(pageTitle) : projectTitle;
      window.document.title = `${projectTitle} - ${finalPageTitle}`;

      const element = window.document.querySelector("meta[name=\"description\"]");
      if (element instanceof HTMLMetaElement) {
        element.content = rootData.node.description;
      }
    } else {
      window.document.title = projectTitle;
    }
  }

  onValidateInitialConfiguration() {
    if (this.appDataService.public.node) {
      if (!this.appDataService.public.node.wizard_done) {
        location.replace("/#/wizard");
      } else if ((this.router.url === "/" || this.router.url === "/submission") && this.appDataService.public.node.adminonly && !this.authenticationService.session) {
        location.replace("/#/admin/home");
      } else if (this.router.url === "/" && this.appDataService.public.node.enable_signup && !location.href.endsWith("admin/home")) {
        location.replace("/#/signup");
      } else if (this.router.url === "/signup" && !this.appDataService.public.node.enable_signup) {
        location.replace("/#/");
      }
    }
  }

  loadAdminRoute(newPath: string) {
    this.appDataService.public.node.wizard_done = true;
    this.appDataService.public.node.languages_enabled = [];
    this.appDataService.public.node.name = "Globaleaks";

    this.router.navigateByUrl(newPath).then(() => {
      this.sidebar = "admin-sidebar";
      this.setTitle();
    });
  }

  routeChangeListener() {
    this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd) {
        this.onValidateInitialConfiguration();
        const lastChildRoute = this.findLastChildRoute(this.router.routerState.root);
        if (lastChildRoute && lastChildRoute.snapshot.data && lastChildRoute.snapshot.data["pageTitle"]) {
          this.header_title = lastChildRoute.snapshot.data["pageTitle"];
          this.sidebar = lastChildRoute.snapshot.data["sidebar"];
          this.setTitle();
        } else {
          this.header_title = "";
          this.sidebar = "";
          this.setTitle();
        }
      }
    });
  }

  findLastChildRoute(route: ActivatedRoute): ActivatedRoute {
    while (route.firstChild) {
      route = route.firstChild;
    }
    return route;
  }

  reinit(languageInit = true) {
    this.localInitialization(languageInit);
  }
}
