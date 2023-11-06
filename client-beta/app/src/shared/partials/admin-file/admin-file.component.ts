import {Component, ElementRef, Input, ViewChild} from "@angular/core";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {UtilsService} from "@app/shared/services/utils.service";
import {AuthenticationService} from "@app/services/authentication.service";
import * as Flow from "@flowjs/flow.js";
import {AppConfigService} from "@app/services/app-config.service";
import {AppDataService} from "@app/app-data.service";

@Component({
  selector: "src-admin-file",
  templateUrl: "./admin-file.component.html"
})
export class AdminFileComponent {
  @Input() adminFile: any;
  nodeData: any = [];
  @ViewChild("uploader") uploaderElementRef!: ElementRef<HTMLInputElement>;

  constructor(protected node: NodeResolver, protected appConfigService: AppConfigService, protected appDataService: AppDataService, protected utilsService: UtilsService, protected authenticationService: AuthenticationService) {
  }

  ngOnInit() {
    this.nodeData["css"] = this.appDataService.public.node.css;
    this.nodeData["script"] = this.appDataService.public.node.script;
    this.nodeData["favicon"] = this.appDataService.public.node.favicon;
  }

  onFileSelected(files: FileList | null, filetype: string) {
    if (files && files.length > 0) {
      const file = files[0];


      const flowJsInstance = new Flow({
        target: "api/admin/files/" + filetype,
        singleFile: true,
        allowDuplicateUploads: false,
        testChunks: false,
        permanentErrors: [500, 501],
        query: {fileSizeLimit: this.node.dataModel.maximum_filesize * 1024 * 1024},
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
        this.appConfigService.reinit(false);
        this.utilsService.reloadCurrentRoute();
      }
    );
  }
}
