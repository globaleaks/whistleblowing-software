import {Component, OnInit} from "@angular/core";
import {WbTipData} from "@app/models/whistleblower/wb-tip-data";
import {WbTipResolver} from "@app/shared/resolvers/wb-tip-resolver.service";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {AppDataService} from "@app/app-data.service";
import {AppConfigService} from "@app/services/root/app-config.service";

@Component({
  selector: "src-receipt-whistleblower",
  templateUrl: "./receipt.component.html"
})
export class ReceiptComponent implements OnInit {
  receipt: string;
  receiptId: string = "";

  constructor(private appConfigService: AppConfigService, private httpService: HttpService, private wbTipResolver: WbTipResolver, protected utilsService: UtilsService, protected authenticationService: AuthenticationService, protected appDataService: AppDataService) {
  }

  public ngOnInit(): void {
    if (this.authenticationService.session.receipt) {
      this.receipt = this.authenticationService.session.receipt;
    } else {
      this.receipt = this.appDataService.receipt;
    }
    this.receiptId = this.receipt.substring(0, 4) + " " + this.receipt.substring(4, 8) + " " + this.receipt.substring(8, 12) + " " + this.receipt.substring(12, 16);
  }

  viewReport(){
    const promise = () => {
      this.httpService.whistleBlowerTip().subscribe(
        (response: WbTipData) => {
          this.wbTipResolver.dataModel = response;
          this.appConfigService.setPage("tippage");
        }
      );
    };
    this.authenticationService.login(0, 'whistleblower', this.receipt, null, null,  promise);
  }

}
