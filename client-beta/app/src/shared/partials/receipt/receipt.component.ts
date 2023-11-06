import {Component, OnInit} from "@angular/core";
import {WbTipData} from "@app/models/whistleblower/wb-tip-data";
import {AuthenticationService} from "@app/services/authentication.service";
import {AppDataService} from "@app/app-data.service";
import {WbTipResolver} from "@app/shared/resolvers/wb-tip-resolver.service";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-receipt",
  templateUrl: "./receipt.component.html"
})
export class ReceiptComponent implements OnInit {
  formattedReceipt = "";

  constructor(private httpService: HttpService, private wbTipResolver: WbTipResolver, protected utilsService: UtilsService, protected authenticationService: AuthenticationService, protected appDataService: AppDataService) {
  }

  ngOnInit(): void {
    // const receipt = this.appDataService.receipt;
    // if (receipt && receipt.length === 16) {
    //   this.formattedReceipt = receipt.substring(0, 4) + " " + receipt.substring(4, 8) + " " + receipt.substring(8, 12) + " " + receipt.substring(12, 16);
    //   return;
    // }
  }

  viewReport(){
    const promise = () => {
      this.httpService.whistleBlowerTip().subscribe(
        (response: WbTipData) => {
          this.wbTipResolver.dataModel = response;
          this.appDataService.page = "tippage";
        }
      );
    };
    this.authenticationService.login(0, 'whistleblower', this.formattedReceipt, null, null,  promise);
  }
}
