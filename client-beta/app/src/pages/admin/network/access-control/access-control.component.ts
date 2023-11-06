import {Component, OnInit} from "@angular/core";
import {NetworkResolver} from "@app/shared/resolvers/network.resolver";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-access-control",
  templateUrl: "./access-control.component.html"
})
export class AccessControlComponent implements OnInit {
  networkData: any;

  constructor(private networkResolver: NetworkResolver, private httpService: HttpService, private utilsService: UtilsService) {
  }

  ngOnInit(): void {
    this.networkData = this.networkResolver.dataModel;
  }

  updateAccessControl(network: any) {
    this.httpService.requestUpdateNetworkResource(network).subscribe(() => {
      this.utilsService.reloadCurrentRoute();
    });
  }
}