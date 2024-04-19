import {HttpClient} from "@angular/common/http";
import {AfterViewInit, Component, ElementRef, Input, OnDestroy, OnInit, ViewChild} from "@angular/core";
import {FlowDirective} from "@flowjs/ngx-flow";
import {Subscription} from "rxjs";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {FlowOptions} from "@flowjs/flow.js";

@Component({
  selector: "src-image-upload",
  templateUrl: "./image-upload.component.html"
})
export class ImageUploadComponent implements AfterViewInit, OnDestroy, OnInit {
  @ViewChild("flowAdvanced")
  flow: FlowDirective;
  @ViewChild("uploader") uploaderElementRef!: ElementRef<HTMLInputElement>;

  @Input() imageUploadModel: { [key: string]: any };
  @Input() imageUploadModelAttr: string;
  @Input() imageUploadId: string;
  imageUploadObj: { files: [] } = {files: []};
  autoUploadSubscription: Subscription;
  filemodel: any;
  currentTImestamp = new Date().getTime();
  flowConfig: FlowOptions;
  @ViewChild('uploader') uploaderInput: ElementRef<HTMLInputElement>;

  constructor(private http: HttpClient, protected authenticationService: AuthenticationService) {
  }

  ngOnInit() {
    this.filemodel = this.imageUploadModel[this.imageUploadModelAttr];
    this.flowConfig = {target: 'api/admin/files/'+this.imageUploadId, speedSmoothingFactor:0.01,singleFile:true ,allowDuplicateUploads:false, testChunks:false, generateUniqueIdentifier: () => {return crypto.randomUUID()}, permanentErrors : [ 500, 501 ], headers : {'X-Session':this.authenticationService.session?.id}}
  }

  ngAfterViewInit() {
    this.autoUploadSubscription = this.flow.events$.subscribe(event => {
      if (event.type === "filesSubmitted") {
        this.imageUploadModel[this.imageUploadModelAttr] = true;
      }
    });
  }

  onFileSelected(files: FileList | null) {
    if (files && files.length > 0) {
      const file = files[0];
      const fileNameParts = file.name.split(".");
      const fileExtension = fileNameParts.pop();
      const fileNameWithoutExtension = fileNameParts.join(".");
      const timestamp = new Date().getTime();
      const fileNameWithTimestamp = `${fileNameWithoutExtension}_${timestamp}.${fileExtension}`;
      const modifiedFile = new File([file], fileNameWithTimestamp, {type: file.type});
      const flowJsInstance = this.flow.flowJs;

      flowJsInstance.addFile(modifiedFile);
      flowJsInstance.upload();
      this.currentTImestamp = new Date().getTime();
      this.filemodel = modifiedFile;
    }
  }

  triggerFileInputClick() {
    this.uploaderElementRef.nativeElement.click();
  }

  ngOnDestroy() {
    this.autoUploadSubscription.unsubscribe();
  }

  deletePicture() {
    this.http
      .delete("api/admin/files/" + this.imageUploadId)
      .subscribe(() => {
        if (this.imageUploadModel) {
          this.imageUploadModel[this.imageUploadModelAttr] = "";
        }
        this.imageUploadObj.files = [];
        this.filemodel = ""
        if (this.uploaderInput) {
          this.uploaderInput.nativeElement.value = "";
        }
      });
  }

  getCurrentTimestamp(): number {
    return this.currentTImestamp;
  }

}
