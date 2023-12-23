import {Component, OnInit} from "@angular/core";
import {WbTipData} from "@app/models/whistleblower/wb-tip-data";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {AppDataService} from "@app/app-data.service";
import {WbTipResolver} from "@app/shared/resolvers/wb-tip-resolver.service";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {Router} from "@angular/router";
import {AppConfigService} from "@app/services/root/app-config.service";

@Component({
  selector: "src-receipt",
  templateUrl: "./receipt.component.html"
})
export class ReceiptComponent implements OnInit {
  formattedReceipt = "";

  constructor(private appConfigService: AppConfigService, private router: Router, private httpService: HttpService, private wbTipResolver: WbTipResolver, protected utilsService: UtilsService, protected authenticationService: AuthenticationService, protected appDataService: AppDataService) {
  }

  ngOnInit(): void {
  }

  viewReport(){
    const promise = () => {
      this.httpService.whistleBlowerTip().subscribe(
        (response: WbTipData) => {
          this.router.navigate(["/"]).then();
          this.wbTipResolver.dataModel = response;
          this.appConfigService.setPage("tippage");
        }
      );
    };
    this.authenticationService.login(0, 'whistleblower', this.formattedReceipt, null, null,  promise);
  }
}
