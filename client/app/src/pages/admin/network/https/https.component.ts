import {Component, OnInit} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import {TlsConfig} from "@app/models/component-model/tls-confiq";
import {Constants} from "@app/shared/constants/constants";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-https",
  templateUrl: "./https.component.html"
})
export class HttpsComponent implements OnInit {
  protected readonly Constants = Constants;
  state = 0;
  menuState = "setup";
  tlsConfig: TlsConfig;
  hostName: string="";

  constructor(protected nodeResolver: NodeResolver, private httpService: HttpService, private utilsService: UtilsService,protected appDataService:AppDataService) {
  }

  ngOnInit() {
    this.initFunction();
    this.hostName = this.appDataService.public.node.hostname
  }

  initFunction() {
    this.httpService.requestTlsConfigResource().subscribe(
      (config: TlsConfig) => {
        this.parseTLSConfig(config);
      }
    );
  }

  updateHostname(hostname: string) {
    this.utilsService.runAdminOperation("set_hostname", {"value": hostname}, true)
      .subscribe(
        () => {
          this.appDataService.public.node.hostname=this.hostName;
        }
      );
  }

  parseTLSConfig(tlsConfig: TlsConfig): void {
    this.tlsConfig = tlsConfig;

    let t = 0;
    let choice = "setup";

    if (!tlsConfig.acme) {
      if (tlsConfig.files.key.set) {
        t = 1;
      }

      if (tlsConfig.files.cert.set) {
        t = 2;
      }

      if (tlsConfig.files.chain.set) {
        t = 3;
      }
    } else if (
      tlsConfig.files.key.set &&
      tlsConfig.files.cert.set &&
      tlsConfig.files.chain.set
    ) {
      t = 3;
    }

    if (tlsConfig.enabled) {
      choice = "status";
      t = -1;
    } else if (t > 0) {
      choice = "files";
    }

    this.state = t;
    this.menuState = choice;
  }

  httpsSetup(data: string) {
    if (data) {
      this.menuState = data;
    }
    if (!data) {
      this.initFunction();
    }
  }

  httpsFiles(data: string) {
    if (data) {
      this.menuState = data;
    }
    if (!data) {
      this.initFunction();
    }
  }

  httpsStatus(data: string) {
    if (data) {
      this.menuState = data;
    }
    if (!data) {
      this.initFunction();
    }
  }
}