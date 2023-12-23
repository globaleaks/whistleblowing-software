import {HttpClient, HttpHeaders} from "@angular/common/http";
import {Component, Input} from "@angular/core";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {ReceiverTipService} from "@app/services/helper/receiver-tip.service";

@Component({
  selector: "src-tip-field-answer-entry",
  templateUrl: "./tip-field-answer-entry.component.html"
})
export class TipFieldAnswerEntryComponent {
  @Input() entry: any;
  @Input() field: any;
  @Input() fieldAnswers: any;
  format = "dd/MM/yyyy";
  locale = "en-US";
  audioFiles: { [key: string]: string } = {};

  constructor(private http: HttpClient, protected authenticationService: AuthenticationService, private tipService: ReceiverTipService) {
  }

  ngOnInit(): void {
    this.loadAudioFile(this.field.id);
  }

  loadAudioFile(reference_id: string): void {
    if (this.tipService.tip.wbfiles) {
      for (const wbfile of this.tipService.tip.wbfiles) {
        if (wbfile.reference_id === reference_id) {
          const id = wbfile.id;

          const headers = new HttpHeaders({
            "x-session": this.authenticationService.session.id
          });

          this.http.get("api/recipient/wbfiles/" + id, {
            headers,
            responseType: "blob"
          })
            .subscribe(response => {
              this.audioFiles[reference_id] = URL.createObjectURL(response);
            });
          break;
        }
      }
    }
  };
}
