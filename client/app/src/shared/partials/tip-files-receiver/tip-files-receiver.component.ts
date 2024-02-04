import {Component, Input, OnInit} from "@angular/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {AppDataService} from "@app/app-data.service";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {HttpService} from "@app/shared/services/http.service";
import {CryptoService} from "@app/shared/services/crypto.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {FileViewComponent} from "@app/shared/modals/file-view/file-view.component";
import {ReceiverTipService} from "@app/services/helper/receiver-tip.service";
import {WbFile} from "@app/models/app/shared-public-model";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {MaskService} from "@app/shared/services/mask.service";
import {RedactionData} from "@app/models/component-model/redaction";
@Component({
  selector: "src-tip-files-receiver",
  templateUrl: "./tip-files-receiver.component.html"
})
export class TipFilesReceiverComponent implements OnInit {
  @Input() fileUploadUrl: string;
  @Input() redactMode: boolean;

  supportedViewTypes = ["application/pdf", "audio/mpeg", "image/gif", "image/jpeg", "image/png", "text/csv", "text/plain", "video/mp4"];
  collapsed = false;

  constructor(protected maskService:MaskService,protected preferenceResolver:PreferenceResolver,protected modalService: NgbModal, private cryptoService: CryptoService, protected httpService: HttpService, protected authenticationService: AuthenticationService, protected utilsService: UtilsService, protected tipService: ReceiverTipService, protected appDataService: AppDataService) {
  }

  ngOnInit(): void {
  }

  public viewRFile(file: WbFile) {
    const modalRef = this.modalService.open(FileViewComponent, {backdrop: 'static', keyboard: false});
    modalRef.componentInstance.args = {
      file: file,
      loaded: false,
      iframeHeight: window.innerHeight * 0.75
    };
  }

  getSortedWBFiles(data: WbFile[]): WbFile[] {
    return data;
  }

  public downloadRFile(file: WbFile) {
    const param = JSON.stringify({});
    this.httpService.requestToken(param).subscribe
    (
      {
        next: async token => {
          this.cryptoService.proofOfWork(token.id).subscribe(
              (ans) => {
                window.open("api/recipient/wbfiles/" + file.id + "?token=" + token.id + ":" + ans);
                this.appDataService.updateShowLoadingPanel(false);
              }
          );
        }
      }
    );
  }

  redactFileOperation(operation: string, content_type: string, file: any) {
    const redactionData:RedactionData= {
      reference_id: file.ifile_id,
      internaltip_id: this.tipService.tip.id,
      entry: "0",
      operation: operation,
      content_type: content_type,
      temporary_redaction: [],
      permanent_redaction: [],
    };

    if (operation === 'full-mask') {
      redactionData.temporary_redaction = [{ start: '-inf', end: 'inf' }];
    }

    const redaction = this.maskService.getRedaction(file.ifile_id, '0', this.tipService.tip);

    if (redaction) {
      redactionData.id = redaction.id;
      this.tipService.updateRedaction(redactionData);
    } else {
      this.tipService.newRedaction(redactionData);
    }
  }
}

