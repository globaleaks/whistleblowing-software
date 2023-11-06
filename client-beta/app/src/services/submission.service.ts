import {Injectable} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import {AuthenticationService} from "@app/services/authentication.service";
import {SubmissionResourceService} from "@app/services/submission-resource.service";
import {HttpService} from "@app/shared/services/http.service";
import {ServiceInstanceService} from "@app/shared/services/service-instance.service";

@Injectable({
  providedIn: "root",
})
export class SubmissionService {
  _submission: any;
  context: any;
  receivers: any[] = [];
  mandatory_receivers = 0;
  optional_receivers = 0;
  selected_receivers: any = {};
  blocked = false;
  uploads: any = {};
  private sharedData: any;

  constructor(protected authenticationService: AuthenticationService, private serviceInstanceService: ServiceInstanceService, private httpService: HttpService, private appDataService: AppDataService, private submissionResourceService: SubmissionResourceService) {
  }

  init() {
    this.authenticationService = this.serviceInstanceService.authenticationService;
  }

  setContextReceivers(context_id: number) {
    this.context = this.appDataService.contexts_by_id[context_id];

    if (Object.keys(this.selected_receivers).length && this.context.allow_recipients_selection) {
      return;
    }

    this.selected_receivers = {};
    this.receivers = [];

    this.context.receivers.forEach((receiver: any) => {
      const r = this.appDataService.receivers_by_id[receiver];

      if (!r) {
        return;
      }

      this.receivers.push(r);

      if (r.forcefully_selected) {
        this.mandatory_receivers += 1;
      } else {
        this.optional_receivers += 1;
      }

      if (this.context.select_all_receivers || r.forcefully_selected) {
        this.selected_receivers[r.id] = true;
      }
    });
  }

  countSelectedReceivers() {
    return Object.keys(this.selected_receivers).length;
  }

  create(context_id: number) {
    this.setContextReceivers(context_id);
    this.submissionResourceService.context_id = context_id;
    this._submission = this.submissionResourceService;
  }

  submit() {
    this._submission.receivers = [];

    for (const key in this.selected_receivers) {
      if (Object.prototype.hasOwnProperty.call(this.selected_receivers, key)) {
        this._submission.receivers.push(key);
      }
    }

    if (!this._submission.identity_provided) {
      this._submission.identity_provided = false;
    }

    const _submission_data = {
      context_id: this._submission.context_id,
      receivers: this._submission.receivers,
      identity_provided: this._submission.identity_provided,
      answers: this._submission.answers,
      answer: this._submission.answer,
      score: this._submission.score,
    };

    const param = JSON.stringify(_submission_data);
    this.httpService.requestReportSubmission(param).subscribe({
      next: (response) => {
        location.pathname = "/";
        this.authenticationService.session.receipt = response.receipt;
        this.appDataService.page = "receiptpage";
      }
    });
  }

  setSharedData(data: any) {
    this.sharedData = data;
  }

  getSharedData(): any {
    return this.sharedData;
  }


}
