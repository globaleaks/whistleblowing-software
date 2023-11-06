import {Component, ElementRef, Input, OnInit, ViewChild} from "@angular/core";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {DomSanitizer, SafeResourceUrl} from "@angular/platform-browser";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-file-view",
  templateUrl: "./file-view.component.html"
})
export class FileViewComponent implements OnInit {
  @Input() args: any;
  @ViewChild("viewer") viewerFrame: ElementRef;

  iframeUrl: SafeResourceUrl;

  constructor(private sanitizer: DomSanitizer, private utilsService: UtilsService, private modalService: NgbModal) {

  }

  ngOnInit() {
    this.iframeUrl = this.sanitizer.bypassSecurityTrustResourceUrl("viewer/index.html");
    this.args.iframeHeight = window.innerHeight * 0.75;
    this.viewFile();
  }

  viewFile() {
    this.utilsService.view("api/recipient/wbfiles/" + this.args.file.id, this.args.file.type, (blob: Blob) => {
      this.args.loaded = true;
      window.addEventListener("message", () => {
        const data = {
          tag: this.getFileTag(this.args.file.type),
          blob: blob
        };
        const iframeElement = this.viewerFrame.nativeElement;
        iframeElement.contentWindow.postMessage(data, "*");

      }, {once: true});
    });
  }

  getFileTag(type: string) {
    if (type === "application/pdf") {
      return "pdf";
    } else if (type.indexOf("audio/") === 0) {
      return "audio";
    } else if (type.indexOf("image/") === 0) {
      return "image";
    } else if (type === "text/csv" || type === "text/plain") {
      return "txt";
    } else if (type.indexOf("video/") === 0) {
      return "video";
    } else {
      return "none";
    }
  };

  cancel() {
    this.modalService.dismissAll();
  }
}
