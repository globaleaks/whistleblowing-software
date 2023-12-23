import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output,
  ViewChild
} from "@angular/core";
import {FlowDirective, Transfer} from "@flowjs/ngx-flow";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {AppDataService} from "@app/app-data.service";
import {ControlContainer, NgForm} from "@angular/forms";
import { Subscription } from "rxjs";
import { FlowOptions } from "@flowjs/flow.js";
import { Field } from "@app/models/resolvers/field-template-model";

@Component({
  selector: "src-rfile-upload-button",
  templateUrl: "./r-file-upload-button.component.html",
  viewProviders: [{provide: ControlContainer, useExisting: NgForm}]
})
export class RFileUploadButtonComponent implements AfterViewInit, OnInit {

  @Input() fileUploadUrl: string;
  @Input() formUploader: boolean = true;
  @Input() uploads: { [key: string]: any };
  @Input() field: Field|undefined = undefined;
  @Output() notifyFileUpload: EventEmitter<any> = new EventEmitter<any>();
  @ViewChild("flow") flow: FlowDirective;

  autoUploadSubscription: Subscription;
  fileInput: string;
  showError: boolean = false;
  errorFile: Transfer;
  confirmButton = false;
  flowConfig: FlowOptions;

  constructor(private cdr: ChangeDetectorRef, protected authenticationService: AuthenticationService, protected appDataService: AppDataService) {
  }

  ngOnInit(): void {
    if (this.authenticationService.session.id) {
      this.flowConfig = {
        target: this.fileUploadUrl,
        speedSmoothingFactor: 0.01,
        singleFile: (this.field !== undefined && !this.field.multi_entry),
        allowDuplicateUploads: false,
        testChunks: false,
        permanentErrors: [500, 501],
        headers: {"X-Session": this.authenticationService.session.id}
      };
    }
    this.fileInput = this.field ? this.field.id : "status_page";
  }

  ngAfterViewInit() {
    const self = this;
    this.autoUploadSubscription = this.flow.transfers$.subscribe((event,) => {

      self.confirmButton = false;
      self.showError = false;

      if (!self.uploads) {
        self.uploads = {};
      }
      if (self.uploads && !self.uploads[self.fileInput]) {
        self.uploads[self.fileInput] = [];
      }
      event.transfers.forEach(function (file) {

        if (file.paused && self.errorFile) {
          self.errorFile.flowFile.cancel();
          return;
        }
        if (self.appDataService.public.node.maximum_filesize < (file.size / 1000000)) {
          self.showError = true;
          self.cdr.detectChanges();
          file.flowFile.pause();
          self.errorFile = file;
        } else if (!file.complete) {
          self.confirmButton = true;
        }
      });
      self.uploads[self.fileInput] = self.flow;
      this.notifyFileUpload.emit(self.uploads);
    });
  }


  ngOnDestroy() {
    this.autoUploadSubscription.unsubscribe();
  }

  onConfirmClick() {
    if (!this.flow.flowJs.isUploading()) {
      this.flow.upload();
    }
  }

  protected dismissError() {
    this.showError = false;
  }
}
