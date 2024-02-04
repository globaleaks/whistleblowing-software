import {HttpClient} from "@angular/common/http";
import {Component, ElementRef, Input, OnInit, ViewChild} from "@angular/core";
import {DomSanitizer, SafeResourceUrl} from "@angular/platform-browser";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import { ReceiverTipService } from "@app/services/helper/receiver-tip.service";
import {WbtipService} from "@app/services/helper/wbtip.service";
import { PreferenceResolver } from "@app/shared/resolvers/preference.resolver";
import { MaskService } from "@app/shared/services/mask.service";

@Component({
  selector: "src-tip-field-answer-entry",
  templateUrl: "./tip-field-answer-entry.component.html"
})
export class TipFieldAnswerEntryComponent implements OnInit {
  @Input() entry: any;
  @Input() field: any;
  @Input() fieldAnswers: any;
  @Input() redactOperationTitle: string;
  @Input() redactMode: boolean;

  format = "dd/MM/yyyy";
  locale = "en-US";
  audioFiles: { [reference_id: string]: Blob } = {};
  iframeUrl: SafeResourceUrl;
  @ViewChild("viewer") viewerFrame: ElementRef;
  tipService:WbtipService|ReceiverTipService;
  constructor(private maskService:MaskService,protected preferenceResolver:PreferenceResolver,private http: HttpClient, private sanitizer: DomSanitizer, protected authenticationService: AuthenticationService, private wbTipService: WbtipService,private rTipService: ReceiverTipService) {
  }

  ngOnInit(): void {
    if (this.authenticationService.session.role === "whistleblower") {
      this.tipService = this.wbTipService;
    }
    if(this.authenticationService.session.role === "receiver") {
      this.tipService = this.rTipService;
    }
    this.iframeUrl = this.sanitizer.bypassSecurityTrustResourceUrl("viewer/index.html");
    this.loadAudioFile(this.field.id);
  }

  loadAudioFile(reference_id: string): void {
     for (const wbfile of this.tipService.tip.wbfiles) {
        if (wbfile.reference_id === reference_id) {
        const id = wbfile.id;
        const url = this.getApiUrl(id);

        this.http.get(url, {
          headers: {
            'x-session': this.authenticationService.session.id
          },
          responseType: 'blob'
        }).subscribe((response: Blob) => {
          this.audioFiles[reference_id] = response;
          window.addEventListener("message", (message: MessageEvent) => {
            const iframe = this.viewerFrame.nativeElement;
            if (message.source !== iframe.contentWindow) {
              return;
            }
            const data = {
              tag: "audio",
              blob: this.audioFiles[reference_id],
            };
            iframe.contentWindow.postMessage(data, "*");
          });
        });

        break;
       }
      }
  }

  private getApiUrl(id: string): string {
    const role = this.authenticationService.session.role;
    return role === 'whistleblower' ?
      `api/whistleblower/wbtip/wbfiles/${id}` :
      `api/recipient/wbfiles/${id}`;
  }

  redactInformation(type:string, id:string, entry:string, content:string){
    this.maskService.redactInfo(type,id,entry,content,this.tipService.tip)
  }

  maskContent(id: string, index: string, value: string) {
   return this.maskService.maskingContent(id,index,value,this.tipService.tip)
  }
}
