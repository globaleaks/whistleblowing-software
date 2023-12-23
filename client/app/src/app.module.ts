import {HostListener, NgModule, CUSTOM_ELEMENTS_SCHEMA} from "@angular/core";
import {BrowserModule} from "@angular/platform-browser";
import {AppRoutingModule} from "@app/app-routing.module";
import {AppComponent} from "@app/pages/app/app.component";
import {HTTP_INTERCEPTORS, HttpClient, HttpClientModule} from "@angular/common/http";
import {AuthModule} from "@app/pages/auth/auth.module";
import {APP_BASE_HREF, HashLocationStrategy, LocationStrategy,} from "@angular/common";
import {SharedModule} from "@app/shared.module";
import {HeaderComponent} from "@app/shared/partials/header/header.component";
import {UserComponent} from "@app/shared/partials/header/template/user/user.component";
import {TranslateLoader, TranslateModule, TranslateService} from "@ngx-translate/core";
import {TranslateHttpLoader} from "@ngx-translate/http-loader";
import {CompletedInterceptor, ErrorCatchingInterceptor, appInterceptor} from "@app/services/root/app-interceptor.service";
import {Keepalive, NgIdleKeepaliveModule} from "@ng-idle/keepalive";
import {DEFAULT_INTERRUPTSOURCES, Idle} from "@ng-idle/core";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {HomeComponent} from "@app/pages/dashboard/home/home.component";
import {TranslatorPipe} from "@app/shared/pipes/translate";
import {NgSelectModule} from "@ng-select/ng-select";
import {FormsModule} from "@angular/forms";
import {ActionModule} from "@app/pages/action/action.module";
import {WhistleblowerModule} from "@app/pages/whistleblower/whistleblower.module";
import {MarkdownModule} from "ngx-markdown";
import {ReceiptValidatorDirective} from "@app/shared/directive/receipt-validator.directive";
import {NgxFlowModule, FlowInjectionToken} from "@flowjs/ngx-flow";
import * as Flow from "@flowjs/flow.js";
import {NgbModule} from "@ng-bootstrap/ng-bootstrap";
import {SignupModule} from "@app/pages/signup/signup.module";
import {WizardModule} from "@app/pages/wizard/wizard.module";
import {RecipientModule} from "@app/pages/recipient/recipient.module";
import {AdminModule} from "@app/pages/admin/admin.module";
import {CustodianModule} from "@app/pages/custodian/custodian.module";
import {BrowserAnimationsModule} from "@angular/platform-browser/animations";

export function createTranslateLoader(http: HttpClient) {
  return new TranslateHttpLoader(http, "l10n/", "");
}

const translationModule = TranslateModule.forRoot({
  loader: {
    provide: TranslateLoader,
    useFactory: createTranslateLoader,
    deps: [HttpClient],
  },
})
;
@NgModule({
  declarations: [AppComponent, HomeComponent, HeaderComponent, UserComponent],
  imports: [
    AppRoutingModule,
    NgbModule,
    HttpClientModule,
    BrowserModule,
    BrowserAnimationsModule,
    AuthModule,
    SignupModule,
    ActionModule,
    WizardModule,
    AdminModule,
    RecipientModule,
    translationModule,
    NgSelectModule,
    FormsModule,
    WhistleblowerModule,
    CustodianModule,
    SharedModule,
    NgIdleKeepaliveModule.forRoot(),
    MarkdownModule.forRoot(),
    NgxFlowModule
  ],
  providers: [
    ReceiptValidatorDirective,
    TranslatorPipe, TranslateService,
    {provide: HTTP_INTERCEPTORS, useClass: appInterceptor, multi: true},
    {provide: APP_BASE_HREF, useValue: "/"},
    {provide: LocationStrategy, useClass: HashLocationStrategy},
    {provide: HTTP_INTERCEPTORS, useClass: ErrorCatchingInterceptor, multi: true},
    {provide: HTTP_INTERCEPTORS, useClass: CompletedInterceptor, multi: true},
    {provide: FlowInjectionToken, useValue: Flow},
    {provide: LocationStrategy, useClass: HashLocationStrategy}
  ],
  bootstrap: [AppComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
})
export class AppModule {

  timedOut = false;
  title = "angular-idle-timeout";

  constructor(private authenticationService: AuthenticationService, private idle: Idle, private keepalive: Keepalive) {
    this.initIdleState();
  }

  @HostListener("window:beforeunload")
  async ngOnDestroy() {
    this.reset();
  }

  initIdleState() {
    this.idle.setIdle(300);
    this.idle.setTimeout(1800);
    this.keepalive.interval(600);
    this.idle.setInterrupts(DEFAULT_INTERRUPTSOURCES);

    this.idle.onTimeout.subscribe(() => {
      if (this.authenticationService && this.authenticationService.session) {
        if (this.authenticationService.session.role === "whistleblower") {
          window.location.replace("about:blank");
        } else {
          this.authenticationService.deleteSession();
          this.authenticationService.loginRedirect();
        }
      }
    });

    this.reset();
  }

  reset() {
    this.idle.watch();
    this.timedOut = false;
    this.authenticationService.reset();
  }
}

