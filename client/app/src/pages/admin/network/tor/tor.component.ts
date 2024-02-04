import {Component, OnInit} from "@angular/core";
import {networkResolverModel} from "@app/models/resolvers/network-resolver-model";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-tor",
  templateUrl: "./tor.component.html"
})
export class TorComponent implements OnInit {
  torOnionResetInProgress: boolean = false;
  networkData: networkResolverModel;

  constructor(protected nodeResolver: NodeResolver, private httpService: HttpService, private utilsService: UtilsService) {
  }

  ngOnInit(): void {
    this.getNetortResolver();
  }

  resetOnionPrivateKey() {
    return this.utilsService.runAdminOperation("reset_onion_private_key", {}, true).subscribe();
  }

  updateTor(network: networkResolverModel) {
    this.httpService.requestUpdateNetworkResource(network).subscribe(() => {
      this.utilsService.reloadComponent();
    });
  }

  getNetortResolver() {
    return this.httpService.requestNetworkResource().subscribe(response => {
        this.networkData = response;
    });
  }
}