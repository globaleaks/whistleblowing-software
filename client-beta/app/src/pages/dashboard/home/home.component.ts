import {Component} from "@angular/core";
import {AppDataService} from "@app/app-data.service";

@Component({
  selector: "src-home",
  templateUrl: "./home.component.html"
})
export class HomeComponent {
  constructor(protected appDataService: AppDataService) {
  }
}
