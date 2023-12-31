import {Component, Input} from "@angular/core";

@Component({
  selector: "src-rfiles-upload-status",
  templateUrl: "./r-files-upload-status.component.html"
})
export class RFilesUploadStatusComponent {
  @Input() uploading: boolean | undefined;
  @Input() progress: number | undefined;
  @Input() estimatedTime: number | undefined;
  protected readonly isFinite = isFinite;
}
