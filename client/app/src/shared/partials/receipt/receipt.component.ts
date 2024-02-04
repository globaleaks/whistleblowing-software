import {Component} from "@angular/core";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {AppDataService} from "@app/app-data.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-receipt",
  templateUrl: "./receipt.component.html"
})
export class ReceiptComponent{
  formattedReceipt = "";

  constructor(protected utilsService: UtilsService, protected authenticationService: AuthenticationService, protected appDataService: AppDataService) {
  }

  viewReport() {
    this.authenticationService.login(0, 'whistleblower', this.formattedReceipt);
    this.formattedReceipt = ""
  }
}
