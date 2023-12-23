import {Component} from "@angular/core";
import {AppDataService} from "@app/app-data.service";

@Component({
  selector: "app-footer",
  templateUrl: "./footer.component.html"
})
export class FooterComponent {
  constructor(protected appDataService: AppDataService) {
  }
}
