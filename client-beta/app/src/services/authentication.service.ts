import {Injectable} from "@angular/core";
import {LoginDataRef} from "@app/pages/auth/login/model/login-model";
import {HttpService} from "@app/shared/services/http.service";
import {Observable} from "rxjs";
import {ActivatedRoute, Router} from "@angular/router";
import {AppDataService} from "@app/app-data.service";
import {ErrorCodes} from "@app/models/app/error-code";
import {AppConfigService} from "@app/services/app-config.service";
import {ServiceInstanceService} from "@app/shared/services/service-instance.service";

@Injectable({
  providedIn: "root"
})
export class AuthenticationService {
  public session: any = undefined;
  public appConfigService: AppConfigService;

  loginInProgress: boolean = false;
  requireAuthCode: boolean = false;
  loginData: LoginDataRef = new LoginDataRef();

  constructor(private appDataService: AppDataService, private serviceInstanceService: ServiceInstanceService, private activatedRoute: ActivatedRoute, private httpService: HttpService, private rootDataService: AppDataService, private router: Router) {
  }

  init() {
    this.appConfigService = this.serviceInstanceService.appConfigService;

    const json = window.sessionStorage.getItem("session");
    if (json !== null) {
      this.session = JSON.parse(json);
    } else {
      this.session = undefined;
    }
  }

  public reset() {
    this.loginInProgress = false;
    this.requireAuthCode = false;
    this.loginData = new LoginDataRef();
  };

  deleteSession() {
    this.session = null;
    window.sessionStorage.removeItem("session");
  };

  isSessionActive() {
    return this.session;
  }

  routeLogin() {
    this.loginRedirect();
  }

  setSession(response: any) {
    this.session = response;
    if (this.session.role !== "whistleblower") {
      const role = this.session.role === "receiver" ? "recipient" : this.session.role;

      this.session.homepage = "/" + role + "/home";
      this.session.preferencespage = "/" + role + "/preferences";
      window.sessionStorage.setItem("session", JSON.stringify(this.session));
    }
  }

  resetPassword(username: string) {
    const param = JSON.stringify({"username": username});
    this.httpService.requestResetLogin(param).subscribe(
      {
        next: () => {
          this.router.navigate(["/login/passwordreset/requested"]).then();
        }
      }
    );
  }

  login(tid?: any, username?: any, password?: any, authcode?: any, authtoken?: any, callback?: () => void) {

    if (authtoken === undefined) {
      authtoken = "";
    }
    if (authcode === undefined) {
      authcode = "";
    }

    let requestObservable: Observable<any>;
    if (authtoken) {
      requestObservable = this.httpService.requestAuthTokenLogin(JSON.stringify({"authtoken": authtoken}));
    } else {
      if (username === "whistleblower") {
        password = password.replace(/\D/g, "");
        const authHeader = this.getHeader();
        requestObservable = this.httpService.requestWhistleBlowerLogin(JSON.stringify({"receipt": password}), authHeader);
      } else {
        requestObservable = this.httpService.requestGeneralLogin(JSON.stringify({
          "tid": tid,
          "username": username,
          "password": password,
          "authcode": authcode
        }));
      }
    }

    requestObservable.subscribe(
      {
        next: (response: any) => {
          this.setSession(response);

          if ("redirect" in response) {
            this.router.navigate([response.data.redirect]).then();
          }

          const src = location.search;
          if (src) {
            location.replace(src);
          } else {
            if (this.session.role === "whistleblower") {
              if (password) {
                this.rootDataService.receipt = password;
              }
            } else {
              if (!callback) {
                this.reset();
                this.rootDataService.showLoadingPanel = true;
                this.router.navigate([this.session.homepage], {
                  queryParams: this.activatedRoute.snapshot.queryParams,
                  queryParamsHandling: "merge"
                }).then();
              }
            }
          }
          if (callback) {
            callback();
          }
        },
        error: (error: any) => {
          this.loginInProgress = false;
          this.rootDataService.showLoadingPanel = false;
          if (error.error && error.error.error_code) {
            if (error.error.error_code === 4) {
              this.requireAuthCode = true;
            } else if (error.error.error_code !== 13) {
              this.reset();
            }
          }

          this.rootDataService.errorCodes = new ErrorCodes(error.error.error_message, error.error.error_code, error.error.arguments);
          if (callback) {
            callback();
          }
        }
      }
    );
    return requestObservable;
  }

  public getHeader(confirmation?: string) {
    const header = new Map<string, string>();
    if (this.session) {
      header.set("X-Session", this.session.id);
      header.set("Accept-Language", "en");
    }
    if (confirmation) {
      header.set("X-Confirmation", confirmation);
    }

    return header;
  }

  logout(callback?: () => void) {
    const requestObservable = this.httpService.requestDeleteUserSession();
    requestObservable.subscribe(
      {
        next: () => {
          this.reset();
          if (this.session.role === "whistleblower") {
            this.deleteSession();
            this.rootDataService.page = "homepage";
          } else {
            this.deleteSession();
            this.loginRedirect();
          }
          if (callback) {
            callback();
          }
        }
      }
    );
  };

  loginRedirect() {
    const source_path = location.pathname;

    if (source_path !== "/login") {
      this.router.navigateByUrl("/login").then();
    }
  };
}
