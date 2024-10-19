import {HostListener, NgModule, CUSTOM_ELEMENTS_SCHEMA, OnDestroy} from "@angular/core";
import {BrowserModule} from "@angular/platform-browser";
import {AppRoutingModule} from "@app/app-routing.module";
import {AppComponent} from "@app/pages/app/app.component";
import {HTTP_INTERCEPTORS, HttpClient, HttpClientModule} from "@angular/common/http";
import {AuthModule} from "@app/pages/auth/auth.module";
import {APP_BASE_HREF, HashLocationStrategy, LocationStrategy, NgOptimizedImage,} from "@angular/common";
import {SharedModule} from "@app/shared.module";
import {HeaderComponent} from "@app/shared/partials/header/header.component";
import {UserComponent} from "@app/shared/partials/header/template/user/user.component";
import {TranslateLoader, TranslateModule, TranslateService} from "@ngx-translate/core";
import {TranslateHttpLoader} from "@ngx-translate/http-loader";
import {
  CompletedInterceptor,
  ErrorCatchingInterceptor,
  appInterceptor
} from "@app/services/root/app-interceptor.service";
import {Keepalive, NgIdleKeepaliveModule} from "@ng-idle/keepalive";
import {DEFAULT_INTERRUPTSOURCES, Idle} from "@ng-idle/core";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {HomeComponent} from "@app/pages/dashboard/home/home.component";
import {TranslatorPipe} from "@app/shared/pipes/translate";
import {NgSelectModule} from "@ng-select/ng-select";
import {FormsModule} from "@angular/forms";
import {ActionModule} from "@app/pages/action/action.module";
import {WhistleblowerModule} from "@app/pages/whistleblower/whistleblower.module";
import {MarkdownModule, MarkedOptions, MARKED_OPTIONS} from "ngx-markdown";
import {ReceiptValidatorDirective} from "@app/shared/directive/receipt-validator.directive";
import {NgxFlowModule, FlowInjectionToken} from "@flowjs/ngx-flow";
import * as Flow from "@flowjs/flow.js";
import {NgbModule, NgbPaginationConfig} from '@ng-bootstrap/ng-bootstrap';
import {SignupModule} from "@app/pages/signup/signup.module";
import {WizardModule} from "@app/pages/wizard/wizard.module";
import {RecipientModule} from "@app/pages/recipient/recipient.module";
import {AdminModule} from "@app/pages/admin/admin.module";
import {CustodianModule} from "@app/pages/custodian/custodian.module";
import {BrowserAnimationsModule} from "@angular/platform-browser/animations";
import {AnalystModule} from "@app/pages/analyst/analyst.module";
import {mockEngine} from './services/helper/mocks';
import {HttpService} from "./shared/services/http.service";
import {CryptoService} from "@app/shared/services/crypto.service";
import {TranslationService} from "@app/services/helper/translation.service";
import {NgbDatepickerI18n} from '@ng-bootstrap/ng-bootstrap';
import {CustomDatepickerI18n} from '@app/shared/services/custom-datepicker-i18n';
import {registerLocales} from '@app/services/helper/locale-provider';
import {ResourceLoaderService} from '@app/services/helper/resource-loader.service';

// Register all the locales
registerLocales();

export function createTranslateLoader(http: HttpClient) {
  return new TranslateHttpLoader(http, "l10n/", "");
}

(window as any).mockEngine = mockEngine;
declare global {
  interface Window {
    GL: {
      language: string;
      mockEngine: any;
    };
  }
}
window.GL = {
  language: 'en', // Assuming a default language
  mockEngine: mockEngine
};

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
    AnalystModule,
    SharedModule,
    NgIdleKeepaliveModule.forRoot(),
    MarkdownModule.forRoot({
      markedOptions: {
        provide: MARKED_OPTIONS,
        useValue: {
          breaks: true
        }
      }
    }),
    NgxFlowModule,
    NgOptimizedImage
  ],
  providers: [
    ReceiptValidatorDirective,
    {provide: 'MockEngine', useValue: mockEngine},
    TranslatorPipe, TranslateService,
    {provide: HTTP_INTERCEPTORS, useClass: appInterceptor, multi: true},
    {provide: APP_BASE_HREF, useValue: "/"},
    {provide: LocationStrategy, useClass: HashLocationStrategy},
    {provide: HTTP_INTERCEPTORS, useClass: ErrorCatchingInterceptor, multi: true},
    {provide: HTTP_INTERCEPTORS, useClass: CompletedInterceptor, multi: true},
    {provide: FlowInjectionToken, useValue: Flow},
    {provide: LocationStrategy, useClass: HashLocationStrategy},
    {
      provide: NgbPaginationConfig,
      useFactory: () => {
        const config = new NgbPaginationConfig();
        config.size = 'sm';           // Set pagination size (sm for small, lg for large)
        config.boundaryLinks = true;  // Display boundary links (first/last)
        config.directionLinks = true; // Display previous/next buttons
        config.maxSize = 20;          // Maximum number of pages displayed
        config.rotate = true;         // Whether to rotate pages when maxSize > number of pages.
        config.ellipses = true;       // If true, the ellipsis symbols and first/last page numbers
                                      // will be shown when maxSize > number of pages.
        return config;
      }
    },
    {provide: NgbDatepickerI18n, useClass: CustomDatepickerI18n}
  ],
  bootstrap: [AppComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
})
export class AppModule implements OnDestroy {

  constructor(private cryptoService:CryptoService, private authenticationService: AuthenticationService, private idle: Idle, private keepalive: Keepalive, private httpService: HttpService, private resourceLoader: ResourceLoaderService) {
    this.initIdleState();
    this.loadNonCriticalResources();
  }

  @HostListener("window:beforeunload")
  async ngOnDestroy() {
    this.reset();
  }

  initIdleState() {
    this.idle.setIdle(1500);
    this.idle.setTimeout(300);
    this.keepalive.interval(30);
    this.idle.setInterrupts(DEFAULT_INTERRUPTSOURCES);

    this.keepalive.onPing.subscribe(() => {
      if (this.authenticationService && this.authenticationService.session) {
        const token = this.authenticationService.session.token;
        this.cryptoService.proofOfWork(token.id).subscribe((result) => {
	  const param = {'token': token.id + ":" + result};
          this.httpService.requestRefreshUserSession(param).subscribe((result => {
            this.authenticationService.session.token = result.token;
	  }));
	});
      }
    });

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

  // Method to load non-critical resources dynamically
  loadNonCriticalResources() {
    // Load CSS file dynamically
    this.resourceLoader.loadStyle('/css/fonts.css');
  }

  reset() {
    this.idle.watch();
    this.authenticationService.reset();
  }
}

