import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {ConfirmationComponent} from "@app/shared/modals/confirmation/confirmation.component";
import {NetworkResolver} from "@app/shared/resolvers/network.resolver";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {HttpService} from "@app/shared/services/http.service";

@Component({
  selector: "src-https-status",
  templateUrl: "./https-status.component.html"
})
export class HttpsStatusComponent implements OnInit {
  @Output() dataToParent = new EventEmitter<string>();
  @Input() tlsConfig: any;
  nodeData: any;

  constructor(private utilsService: UtilsService, protected networkResolver: NetworkResolver, private nodeResolver: NodeResolver, private httpService: HttpService, private modalService: NgbModal) {
  }

  ngOnInit(): void {
    this.nodeData = this.nodeResolver.dataModel;
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