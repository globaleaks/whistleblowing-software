import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {ConfirmationComponent} from "@app/shared/modals/confirmation/confirmation.component";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {nodeResolverModel} from "@app/models/resolvers/node-resolver-model";
import {TlsConfig} from "@app/models/component-model/tls-confiq";
import {FileResource, FileResources} from "@app/models/component-model/file-resources";

@Component({
  selector: "src-https-files",
  templateUrl: "./https-files.component.html"
})
export class HttpsFilesComponent implements OnInit {
  @Output() dataToParent = new EventEmitter<string>();
  @Input() tlsConfig: TlsConfig;
  @Input() state: number = 0;
  nodeData: nodeResolverModel;
  fileResources: FileResources = {
    key: {name: "key"},
    cert: {name: "cert"},
    chain: {name: "chain"},
    csr: {name: "csr"},
  };
  csr_state = {
    open: false
  };

  constructor(private authenticationService: AuthenticationService, private nodeResolver: NodeResolver, private httpService: HttpService, private modalService: NgbModal, private utilsService: UtilsService) {
  }

  ngOnInit(): void {
    this.nodeData = this.nodeResolver.dataModel;
  }

  postFile(files: FileList | null, resource: FileResource) {
    if (files && files.length > 0) {
      const file = files[0];
      this.utilsService.readFileAsText(file).subscribe(
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
  }

  genKey() {
    const authHeader = this.authenticationService.getHeader();
    this.httpService.requestUpdateTlsConfigFilesResource("key", authHeader, this.fileResources.key).subscribe(() => {
      this.dataToParent.emit();
    });
  }

  deleteFile(fileResource: FileResource) {
    const modalRef = this.modalService.open(ConfirmationComponent, {backdrop: 'static', keyboard: false});
    modalRef.componentInstance.arg = fileResource.name;
    modalRef.componentInstance.confirmFunction = (arg: string) => {
      return this.httpService.requestDeleteTlsConfigFilesResource(arg).subscribe(() => {
        this.dataToParent.emit();
      });
    };
    return modalRef.result;
  }

  downloadCSR() {
    this.httpService.downloadCSRFile().subscribe(
      (response: Blob) => {
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
    this.utilsService.toggleCfg(this.authenticationService, this.tlsConfig, this.dataToParent);
  }

  resetCfg() {
    const modalRef = this.modalService.open(ConfirmationComponent, {backdrop: 'static', keyboard: false});
    modalRef.componentInstance.arg = null;
    modalRef.componentInstance.confirmFunction = () => {
      return this.httpService.requestDeleteTlsConfigResource().subscribe(() => {
        this.dataToParent.emit();
      });
    };
    return modalRef.result;
  }
}