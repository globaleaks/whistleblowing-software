import {Component, EventEmitter, Output} from "@angular/core";
import {AuthenticationService} from "@app/services/authentication.service";
import {HttpService} from "@app/shared/services/http.service";

@Component({
  selector: "src-https-setup",
  templateUrl: "./https-setup.component.html"
})
export class HttpsSetupComponent {
  @Output() dataToParent = new EventEmitter<string>();
  fileResources: {
    key: any,
    cert: any,
    chain: any,
    csr: any,
  };

  constructor(private httpService: HttpService, private authenticationService: AuthenticationService) {
    this.fileResources = {
      key: {name: "key"},
      cert: {name: "cert"},
      chain: {name: "chain"},
      csr: {name: "csr"},
    };
  }

  setupAcme() {
    const authHeader = this.authenticationService.getHeader();
    this.httpService.requestUpdateTlsConfigFilesResource("key", authHeader, this.fileResources.key).subscribe(() => {
      this.httpService.requestAdminAcmeResource({}, authHeader).subscribe(() => {
        this.dataToParent.emit();
      });
    });
  }

  setup() {
    this.dataToParent.emit("files");
  }
}