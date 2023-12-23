import {Component} from "@angular/core";
import {AppConfigService} from "@app/services/root/app-config.service";
import {AppDataService} from "@app/app-data.service";

@Component({
  selector: "views-header",
  templateUrl: "./header.component.html"
})
export class HeaderComponent {
  constructor(public appConfig: AppConfigService, public appDataService: AppDataService) {
  }
}
