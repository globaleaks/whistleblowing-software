import {Component, EventEmitter, Output} from "@angular/core";
import {FileResources} from "@app/models/component-model/file-resources";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {HttpService} from "@app/shared/services/http.service";

@Component({
  selector: "src-https-setup",
  templateUrl: "./https-setup.component.html"
})
export class HttpsSetupComponent {
  @Output() dataToParent = new EventEmitter<string>();
  fileResources:FileResources = {
    key: {name: "key"},
    cert: {name: "cert"},
    chain: {name: "chain"},
    csr: {name: "csr"},
  };
  constructor(private httpService: HttpService, private authenticationService: AuthenticationService) {
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