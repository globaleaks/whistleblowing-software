import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {AuthenticationService} from "@app/services/authentication.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {ConfirmationComponent} from "@app/shared/modals/confirmation/confirmation.component";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-https-files",
  templateUrl: "./https-files.component.html"
})
export class HttpsFilesComponent implements OnInit {
  @Output() dataToParent = new EventEmitter<string>();
  @Input() tlsConfig: any;
  @Input() state: number = 0;
  menuState: string;
  nodeData: any;
  fileResources: {
    key: any,
    cert: any,
    chain: any,
    csr: any,
  };
  csr_state = {
    open: false
  };

  constructor(private authenticationService: AuthenticationService, private nodeResolver: NodeResolver, private httpService: HttpService, private modalService: NgbModal, private utilsService: UtilsService) {
    this.fileResources = {
      key: {name: "key"},
      cert: {name: "cert"},
      chain: {name: "chain"},
      csr: {name: "csr"},
    };
  }

  ngOnInit(): void {
    this.nodeData = this.nodeResolver.dataModel;
  }

  postFile(file: any, resource: any) {
    this.utilsService.readFileAsText(file[0]).then(
      (str: string) => {
        resource.content = str;
        this.httpService.requestCSRContentResource(resource.name, resource).subscribe(
          () => {
            this.dataToParent.emit();
          }
        );
      },
    );
  }

  genKey() {
    const authHeader = this.authenticationService.getHeader();
    this.httpService.requestUpdateTlsConfigFilesResource("key", authHeader, this.fileResources.key).subscribe(() => {
      this.dataToParent.emit();
    });
  }

  deleteFile(fileResource: any) {
    const modalRef = this.modalService.open(ConfirmationComponent);
    modalRef.componentInstance.arg = fileResource.name;
    modalRef.componentInstance.confirmFunction = (arg: any) => {
      return this.httpService.requestDeleteTlsConfigFilesResource(arg).subscribe(() => {
        this.dataToParent.emit();
      });
    };
    return modalRef.result;
  }

  httpsCsr(data: any) {
    this.fileResources = data;
    this.csr_state.open = false;
    this.dataToParent.emit();
  }

  downloadCSR() {
    this.httpService.downloadCSRFile().subscribe(
      (response: any) => {
        const blob = new Blob([response], {type: "application/octet-stream"});
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "csr.pem";
        link.click();
        window.URL.revokeObjectURL(url);
      },
    );
  }

  toggleCfg() {
    this.utilsService.toggleCfg(this.tlsConfig, this.dataToParent);
  }

  resetCfg() {
    const modalRef = this.modalService.open(ConfirmationComponent);
    modalRef.componentInstance.arg = null;
    modalRef.componentInstance.confirmFunction = (_: any) => {
      return this.httpService.requestDeleteTlsConfigResource().subscribe(() => {
        this.dataToParent.emit();
      });
    };
    return modalRef.result;
  }
}