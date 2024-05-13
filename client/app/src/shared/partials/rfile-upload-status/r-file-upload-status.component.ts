import {Component, Input} from "@angular/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {AppDataService} from "@app/app-data.service";
import {Transfer} from "@flowjs/ngx-flow";

@Component({
  selector: "src-rfile-upload-status",
  templateUrl: "./r-file-upload-status.component.html"
})
export class RFileUploadStatusComponent {
  @Input() file: Transfer;
  @Input() formUploader: boolean;

  constructor(protected utilsService: UtilsService, protected appDataService: AppDataService) {
  }
}
