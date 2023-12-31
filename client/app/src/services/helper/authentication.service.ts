import {Injectable} from "@angular/core";
import {LoginDataRef} from "@app/pages/auth/login/model/login-model";
import {HttpService} from "@app/shared/services/http.service";
import {Observable} from "rxjs";
import {ActivatedRoute, Router} from "@angular/router";
import {AppDataService} from "@app/app-data.service";
import {ErrorCodes} from "@app/models/app/error-code";
import {Session} from "@app/models/authentication/session";
import {TitleService} from "@app/shared/services/title.service";
import {HttpHeaders} from "@angular/common/http";

@Injectable({
  providedIn: "root"
})
export class AuthenticationService {
  public session: any = undefined;
  permissions: { can_upload_files: boolean }
  loginInProgress: boolean = false;
  requireAuthCode: boolean = false;
  loginData: LoginDataRef = new LoginDataRef();

  constructor(private titleService: TitleService, private activatedRoute: ActivatedRoute, private httpService: HttpService, private appDataService: AppDataService, private router: Router) {
    this.init();
  }

  init() {
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

  setSession(response: Session) {
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

  login(tid?: number, username?: string, password?: string | undefined, authcode?: string | null, authtoken?: string | null, callback?: () => void) {

    if (authtoken === undefined) {
      authtoken = "";
    }
    if (authcode === undefined) {
      authcode = "";
    }

    let requestObservable: Observable<Session>;
    if (authtoken) {
      requestObservable = this.httpService.requestAuthTokenLogin(JSON.stringify({"authtoken": authtoken}));
    } else {
      if (username === "whistleblower") {
        password = password?.replace(/\D/g, "");
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
        next: (response: Session) => {
          this.setSession(response);

          if (response.redirect) {
            this.router.navigate([response.redirect]).then();
          }

          const src = location.search;
          if (src) {
            location.replace(src);
          } else {
            if (this.session.role === "whistleblower") {
              if (password) {
                this.appDataService.receipt = password;
              }
            } else {
              if (!callback) {
                this.reset();
                this.appDataService.updateShowLoadingPanel(true);
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
        error: (error) => {
          this.loginInProgress = false;
          this.appDataService.updateShowLoadingPanel(false);
          if (error.error && error.error.error_code) {
            if (error.error.error_code === 4) {
              this.requireAuthCode = true;
            } else if (error.error.error_code !== 13) {
              this.reset();
            }
          }

          this.appDataService.errorCodes = new ErrorCodes(error.error.error_message, error.error.error_code, error.error.arguments);
          if (callback) {
            callback();
          }
        }
      }
    );
    return requestObservable;
  }

  public getHeader(confirmation?: string): HttpHeaders {
    let headers = new HttpHeaders();

    if (this.session) {
      headers = headers.set('X-Session', this.session.id);
      headers = headers.set('Accept-Language', 'en');
    }

    if (confirmation) {
      headers = headers.set('X-Confirmation', confirmation);
    }
    return headers;
  }

  logout(callback?: () => void) {
    const requestObservable = this.httpService.requestDeleteUserSession();
    requestObservable.subscribe(
      {
        next: () => {
          this.reset();
          if (this.session.role === "whistleblower") {
            this.deleteSession();
            this.titleService.setPage("homepage");
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
