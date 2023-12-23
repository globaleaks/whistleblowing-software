import {Component} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-privacybadge",
  templateUrl: "./privacy-badge.component.html"
})
export class PrivacyBadgeComponent {
  public markdown: string;

  constructor(protected appDataService: AppDataService, protected utilsService: UtilsService) {
    this.markdown = appDataService.public.node.custom_privacy_badge_text;
  }

}
