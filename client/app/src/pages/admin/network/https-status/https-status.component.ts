import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {ConfirmationComponent} from "@app/shared/modals/confirmation/confirmation.component";
import {NetworkResolver} from "@app/shared/resolvers/network.resolver";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {HttpService} from "@app/shared/services/http.service";
import {nodeResolverModel} from "@app/models/resolvers/node-resolver-model";
import {TlsConfig} from "@app/models/component-model/tls-confiq";
import {AuthenticationService} from "@app/services/helper/authentication.service";

@Component({
  selector: "src-https-status",
  templateUrl: "./https-status.component.html"
})
export class HttpsStatusComponent implements OnInit {
  @Output() dataToParent = new EventEmitter<string>();
  @Input() tlsConfig: TlsConfig;
  nodeData: nodeResolverModel;

  constructor(private authenticationService: AuthenticationService, private utilsService: UtilsService, protected networkResolver: NetworkResolver, private nodeResolver: NodeResolver, private httpService: HttpService, private modalService: NgbModal) {
  }

  ngOnInit(): void {
    this.nodeData = this.nodeResolver.dataModel;
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

  getNetworkResolver() {
    return "https://" + this.networkResolver.dataModel.hostname
  }
}