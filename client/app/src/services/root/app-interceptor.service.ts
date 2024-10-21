import { Injectable, inject } from "@angular/core";
import {
  HttpInterceptor,
  HttpEvent,
  HttpRequest,
  HttpHandler,
  HttpClient,
  HttpErrorResponse,
} from "@angular/common/http";
import {catchError, finalize, from, Observable, switchMap, throwError} from "rxjs";
import {TokenResponse} from "@app/models/authentication/token-response";
import {CryptoService} from "@app/shared/services/crypto.service";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {AppDataService} from "@app/app-data.service";
import {TranslationService} from "@app/services/helper/translation.service";
import {ErrorCodes} from "@app/models/app/error-code";
import {of} from 'rxjs';
import {timer} from 'rxjs';

const protectedUrls = [
  "api/wizard",
  "api/auth/tokenauth",
  "api/auth/authentication",
  "api/user/reset/password",
  "api/recipient/rtip",
  "api/support"
];

@Injectable()
export class appInterceptor implements HttpInterceptor {
  private authenticationService = inject(AuthenticationService);
  private httpClient = inject(HttpClient);
  private cryptoService = inject(CryptoService);
  private translationService = inject(TranslationService);


  private getAcceptLanguageHeader(): string | null {
    if (this.translationService.language) {
      return this.translationService.language;
    } else {
      const url = window.location.href;
      const hashFragment = url.split("#")[1];

      if (hashFragment && hashFragment.includes("lang=")) {
        return hashFragment.split("lang=")[1].split("&")[0];
      } else {
        return "";
      }
    }
  }

  intercept(httpRequest: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {

    if (httpRequest.url.endsWith("/data/i18n/.json")) {
      return next.handle(httpRequest);
    }

    const authHeader = this.authenticationService.getHeader();
    let authRequest = httpRequest;

    authHeader.keys().forEach(header => {
      const headerValue = authHeader.get(header);
      if (headerValue) {
        authRequest = authRequest.clone({headers: authRequest.headers.set(header, headerValue)});
      }
    });

    authRequest = authRequest.clone({
      headers: authRequest.headers.set("Accept-Language", this.getAcceptLanguageHeader() || ""),
    });

    if (httpRequest.url.includes("api/signup") || httpRequest.url.endsWith("api/auth/receiptauth") && !this.authenticationService.session || protectedUrls.includes(httpRequest.url)) {
      return this.httpClient.post("api/auth/token", {}).pipe(
        switchMap((response) =>
          from(this.cryptoService.proofOfWork(Object.assign(new TokenResponse(), response).id)).pipe(
            switchMap((ans) => next.handle(httpRequest.clone({
              headers: httpRequest.headers.set("x-token", `${Object.assign(new TokenResponse(), response).id}:${ans}`)
                .set("Accept-Language", this.getAcceptLanguageHeader() || ""),
            })))
          )
        )
      );
    } else {
      return next.handle(authRequest);
    }
  }
}

@Injectable()
export class ErrorCatchingInterceptor implements HttpInterceptor {
  private authenticationService = inject(AuthenticationService);
  private appDataService = inject(AppDataService);


  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {

    return next.handle(request)
      .pipe(
        catchError((error: HttpErrorResponse) => {
          if(error.error){
            if (error.error["error_code"] === 10) {
              this.authenticationService.deleteSession();
              this.authenticationService.reset();
              this.authenticationService.routeLogin();
            } else if (error.error["error_code"] === 6 && this.authenticationService.isSessionActive()) {
              if (this.authenticationService.session.role !== "whistleblower") {
                location.pathname = this.authenticationService.session.homepage;
              }
            }
            this.appDataService.errorCodes = new ErrorCodes(error.error["error_message"], error.error["error_code"], error.error["arguments"]);
          }
          return throwError(() => error);
        })
      );
  }
}

@Injectable()
export class CompletedInterceptor implements HttpInterceptor {
  private appDataService = inject(AppDataService);

  count = 0;

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    if (req.url !== "api/auth/authentication") {
      this.count++;
      this.appDataService.updateShowLoadingPanel(true);
    }

    return next.handle(req).pipe(
      finalize(() => {
        if (req.url !== "api/auth/authentication") {
          this.count--;
          if (this.count === 0 && (req.url !== "api/auth/token")) {
            timer(100).pipe(
              switchMap(() => {
                this.appDataService.updateShowLoadingPanel(false);
                return of(null);
              })
            ).subscribe();
          }
        }
      })
    );
  }
}
