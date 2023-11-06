import {Component} from "@angular/core";
import {AppConfigService} from "@app/services/app-config.service";
import {AppDataService} from "@app/app-data.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {TranslateService} from "@ngx-translate/core";
import {NavigationEnd, Router} from "@angular/router";

@Component({
  selector: "app-root",
  templateUrl: "./app.component.html"
})
export class AppComponent {
  showSidebar: boolean = true;
  isNavCollapsed: boolean = true;

  constructor(private router: Router, protected translate: TranslateService, protected appConfig: AppConfigService, protected appDataService: AppDataService, protected utilsService: UtilsService) {
  }

  checkToShowSidebar() {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        const excludedUrls = [
          "/recipient/reports"
        ];
        const currentUrl = event.url;
        this.showSidebar = !excludedUrls.includes(currentUrl);
      }
    });
  }

  ngOnInit() {
    this.appConfig.routeChangeListener();
    this.checkToShowSidebar();
  }

  public openGithubReport() {
    window.open("https://github.com/msmannan00/globaleaks-angular-fork/issues", "_blank");
  }
}
