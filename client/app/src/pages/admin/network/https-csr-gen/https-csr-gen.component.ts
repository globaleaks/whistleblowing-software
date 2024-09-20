import {Component, Input} from "@angular/core";
import {FileResources} from "@app/models/component-model/file-resources";
import {Constants} from "@app/shared/constants/constants";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {AuthenticationService} from "@app/services/helper/authentication.service";

@Component({
  selector: "src-https-csr-gen",
  templateUrl: "./https-csr-gen.component.html"
})
export class HttpsCsrGenComponent {
  @Input() fileResources: FileResources;
  protected readonly Constants = Constants;
  csr_cfg: {
    country: string;
    province: string;
    city: string;
    company: string;
    department: string;
    email: string;
  } = {
    country: "",
    province: "",
    city: "",
    company: "",
    department: "",
    email: ""
  };

  constructor(private authenticationService: AuthenticationService, private httpService: HttpService, private utilsService: UtilsService) {
  }

  submitCSR() {
    this.httpService.requestCSRDirectContentResource(this.csr_cfg).subscribe({
      next: (response) => {
        this.utilsService.saveBlobAs("csr.pem", new Blob([response.data]));
      },
      error: (error: any) => {
        if (error.status === 201) {
          const errorText = error.error.text;
          this.utilsService.saveBlobAs("csr.pem", new Blob([errorText]));
        }
      }
    });
  }

}