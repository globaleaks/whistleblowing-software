import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {NetworkResolver} from "@app/shared/resolvers/network.resolver";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {nodeResolverModel} from "@app/models/resolvers/node-resolver-model";
import {TlsConfig} from "@app/models/component-model/tls-confiq";

@Component({
  selector: "src-https-status",
  templateUrl: "./https-status.component.html"
})
export class HttpsStatusComponent implements OnInit {
  @Output() dataToParent = new EventEmitter<string>();
  @Input() tlsConfig: TlsConfig;
  nodeData: nodeResolverModel;

  constructor(protected networkResolver: NetworkResolver, private nodeResolver: NodeResolver) {
  }

  ngOnInit(): void {
    this.nodeData = this.nodeResolver.dataModel;
  }

  getNetworkResolver(){
    return "https://" + this.networkResolver.dataModel.hostname
  }
}
