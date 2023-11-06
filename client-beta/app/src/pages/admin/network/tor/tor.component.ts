import {Component, OnInit} from "@angular/core";
import {NetworkResolver} from "@app/shared/resolvers/network.resolver";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-tor",
  templateUrl: "./tor.component.html"
})
export class TorComponent implements OnInit {
  torOnionResetInProgress: boolean = false;
  networkData: any;

  constructor(protected nodeResolver: NodeResolver, private networkResolver: NetworkResolver, private httpService: HttpService, private utilsService: UtilsService) {
  }

  ngOnInit(): void {
    this.networkData = this.networkResolver.dataModel;
  }

  resetOnionPrivateKey() {
    return this.utilsService.runAdminOperation("reset_onion_private_key", {}, true).subscribe();
  }

  updateTor(network: any) {
    this.httpService.requestUpdateNetworkResource(network).subscribe(() => {
      this.utilsService.reloadCurrentRoute();
    });
  }
}