import {Component, Input, OnInit} from "@angular/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {AppDataService} from "@app/app-data.service";
import {AuthenticationService} from "@app/services/authentication.service";
import {HttpService} from "@app/shared/services/http.service";
import {CryptoService} from "@app/crypto.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {FileViewComponent} from "@app/shared/modals/file-view/file-view.component";
import {ReceiverTipService} from "@app/services/receiver-tip.service";

@Component({
  selector: "src-tip-files-receiver",
  templateUrl: "./tip-files-receiver.component.html"
})
export class TipFilesReceiverComponent implements OnInit {
  @Input() fileUploadUrl: any;
  supportedViewTypes = ["application/pdf", "audio/mpeg", "image/gif", "image/jpeg", "image/png", "text/csv", "text/plain", "video/mp4"];
  collapsed = false;

  constructor(protected modalService: NgbModal, private cryptoService: CryptoService, protected httpService: HttpService, protected authenticationService: AuthenticationService, protected utilsService: UtilsService, protected tipService: ReceiverTipService, protected appDataService: AppDataService) {
  }

  ngOnInit(): void {
  }

  public viewRFile(file: any) {
    const modalRef = this.modalService.open(FileViewComponent);
    modalRef.componentInstance.args = {
      file: file,
      loaded: false,
      iframeHeight: window.innerHeight * 0.75
    };
  }

  public downloadRFile(file: any) {
    const param = JSON.stringify({});
    this.httpService.requestToken(param).subscribe
    (
      {
        next: async token => {
          const ans = await this.cryptoService.proofOfWork(token.id);
          window.open("api/recipient/wbfiles/" + file.id + "?token=" + token.id + ":" + ans);
          this.appDataService.showLoadingPanel = false;
        }
      }
    );
  }
}