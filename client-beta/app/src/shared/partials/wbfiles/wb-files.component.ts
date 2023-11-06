import {Component, Input, OnInit} from "@angular/core";
import {AuthenticationService} from "@app/services/authentication.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {HttpService} from "@app/shared/services/http.service";
import {CryptoService} from "@app/crypto.service";

@Component({
  selector: "src-wbfiles",
  templateUrl: "./wb-files.component.html"
})
export class WbFilesComponent implements OnInit {
  @Input() wbFile: any;
  @Input() ctx: any;
  @Input() receivers_by_id: any;

  constructor(private cryptoService: CryptoService, private httpService: HttpService, private utilsService: UtilsService, protected authenticationService: AuthenticationService) {
  }

  ngOnInit(): void {
  }

  deleteWBFile(wbFile: any) {
    if (this.authenticationService.session.role === "receiver") {
      this.httpService.deleteDBFile(wbFile.id).subscribe
      (
        {
          next: async _ => {
            this.utilsService.reloadCurrentRoute();
          }
        }
      );
    }
  }

  downloadWBFile(wbFile: any) {

    const param = JSON.stringify({});
    this.httpService.requestToken(param).subscribe
    (
      {
        next: async token => {
          const ans = await this.cryptoService.proofOfWork(token.id);
          if (this.authenticationService.session.role === "receiver") {
            window.open("api/recipient/rfiles/" + wbFile.id + "?token=" + token.id + ":" + ans);
          } else {
            window.open("api/whistleblower/wbtip/rfiles/" + wbFile.id + "?token=" + token.id + ":" + ans);
          }
        }
      }
    );
  }
}
