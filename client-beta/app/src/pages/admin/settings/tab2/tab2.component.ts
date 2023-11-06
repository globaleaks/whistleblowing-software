import {Component, ElementRef, Input, OnInit, ViewChild} from "@angular/core";
import {NgForm} from "@angular/forms";
import * as Flow from "@flowjs/flow.js";
import type {FlowFile} from "@flowjs/flow.js";
import {FlowDirective} from "@flowjs/ngx-flow";
import {AuthenticationService} from "@app/services/authentication.service";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {UtilsService} from "@app/shared/services/utils.service";
import {Subscription} from "rxjs";
import {AppConfigService} from "@app/services/app-config.service";

@Component({
  selector: "src-tab2",
  templateUrl: "./tab2.component.html"
})
export class Tab2Component implements OnInit {
  @Input() contentForm: NgForm;
  @ViewChild("flowAdvanced", {static: true}) flowAdvanced: FlowDirective;
  @ViewChild("uploader") uploader: ElementRef;

  files: FlowFile[] = [];
  flow: FlowDirective;
  flowConfig: any = {};
  autoUploadSubscription: Subscription;
  preferenceData: any = [];
  authenticationData: any = [];

  admin_files: any[] = [
    {
      "title": "Favicon",
      "varname": "favicon",
      "filename": "custom_favicon.ico",
      "size": "200000"
    },
    {
      "title": "CSS",
      "varname": "css",
      "filename": "custom_stylesheet.css",
      "size": "10000000"
    },
    {
      "title": "JavaScript",
      "varname": "script",
      "filename": "custom_script.js",
      "size": "10000000"
    }
  ];

  constructor(private appConfigService: AppConfigService, private preferenceResolver: PreferenceResolver, private utilsService: UtilsService, private nodeResolver: NodeResolver, private authenticationService: AuthenticationService) {
  }

  ngOnInit(): void {
    this.preferenceData = this.preferenceResolver.dataModel;
    this.authenticationData = this.authenticationService;
    this.authenticationData.permissions = {
      can_upload_files: false
    };
    this.preferenceData.permissions = {
      can_upload_files: false
    };
    this.updateFiles();
  }

  onFileSelected(files: FileList | null) {
    if (files && files.length > 0) {
      const file = files[0];

      const flowJsInstance = new Flow({
        target: "api/admin/files/custom",
        speedSmoothingFactor: 0.01,
        singleFile: true,
        allowDuplicateUploads: false,
        testChunks: false,
        permanentErrors: [500, 501],
        query: {fileSizeLimit: this.nodeResolver.dataModel.maximum_filesize * 1024 * 1024},
        headers: {"X-Session": this.authenticationService.session.id}
      });

      flowJsInstance.on("fileSuccess", (_) => {
        this.appConfigService.reinit(false);
        this.utilsService.reloadCurrentRoute();
      });
      this.utilsService.onFlowUpload(flowJsInstance, file)
    }
  }

  deleteFile(url: string): void {
    this.utilsService.deleteFile(url).subscribe(
      () => {
        this.updateFiles();
        this.utilsService.init();
        this.utilsService.reloadCurrentRoute();
      }
    );
  }

  updateFiles(): void {
    this.utilsService.getFiles().subscribe(
      (updatedFiles) => {
        this.files = updatedFiles;
      }
    );
  }

  togglePermissionUploadFiles(status: any): void {

    this.authenticationData.session.permissions.can_upload_files = !this.authenticationData.session.permissions.can_upload_files;
    status.checked = this.authenticationData.session.permissions.can_upload_files;

    if (!this.authenticationData.session.permissions.can_upload_files) {
      this.utilsService.runAdminOperation("enable_user_permission_file_upload", {}, false).subscribe({
        next: (_) => {
          this.authenticationData.session.permissions.can_upload_files = true;
          status.checked = true;
        },
        error: (_: any) => {
          this.authenticationData.session.permissions.can_upload_files = false;
          status.checked = false;
          status.click();
        }
      });
    } else {
      this.utilsService.runAdminOperation("disable_user_permission_file_upload", {}, false).subscribe(
        () => {
          this.authenticationData.session.permissions.can_upload_files = false;
          status.checked = false;
        }
      );
    }
  }
}