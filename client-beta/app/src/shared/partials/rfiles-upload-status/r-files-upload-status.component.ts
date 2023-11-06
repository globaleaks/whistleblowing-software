import {Component, Input} from "@angular/core";

@Component({
  selector: "src-rfiles-upload-status",
  templateUrl: "./r-files-upload-status.component.html"
})
export class RFilesUploadStatusComponent {
  @Input() uploading: any;
  @Input() progress: any;
  @Input() estimatedTime: any;
  protected readonly isFinite = isFinite;
}
