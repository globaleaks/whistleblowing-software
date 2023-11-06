import {Component} from "@angular/core";
import {WbTipResolver} from "@app/shared/resolvers/wb-tip-resolver.service";
import {FieldUtilitiesService} from "@app/shared/services/field-utilities.service";
import {ActivatedRoute} from "@angular/router";
import {HttpService} from "@app/shared/services/http.service";
import {WbtipService} from "@app/services/wbtip.service";
import {AppDataService} from "@app/app-data.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-tippage",
  templateUrl: "./tippage.component.html"
})
export class TippageComponent {

  fileUploadUrl: string;
  tip_id = null;
  answers = {};
  uploads: any = {};
  score = 0;
  ctx: string;
  rows: any;
  questionnaire: any;
  questionnaires: any;
  identity_provided = false;

  private submission: any;
  protected tip: any;

  constructor(private fieldUtilities: FieldUtilitiesService, private wbTipResolver: WbTipResolver, private fieldUtilitiesService: FieldUtilitiesService, protected utilsService: UtilsService, protected appDataService: AppDataService, private activatedRoute: ActivatedRoute, private httpService: HttpService, protected wbTipService: WbtipService) {
  }

  ngOnInit() {
    let wpTip = this.wbTipResolver.dataModel;
    if (wpTip) {
      this.wbTipService.initialize(wpTip);
      this.tip = this.wbTipService.tip;

      this.activatedRoute.queryParams.subscribe(params => {
        this.tip.tip_id = params["tip_id"];
      });

      this.fileUploadUrl = "api/whistleblower/wbtip/wbfiles";
      this.tip.context = this.appDataService.contexts_by_id[this.tip.context_id];

      this.tip.receivers_by_id = this.utilsService.array_to_map(this.tip.receivers);
      this.score = this.tip.score;
      this.ctx = "wbtip";
      this.preprocessTipAnswers(this.tip);

      this.tip.submissionStatusStr = this.utilsService.getSubmissionStatusText(this.tip.status, this.appDataService.submissionStatuses);
      this.submission = {};
      this.submission._submission = this.tip;
      if (this.tip.receivers.length === 1 && this.tip.msg_receiver_selected === null) {
        this.tip.msg_receiver_selected = this.tip.msg_receivers_selector[0].key;
      }
    } else {
      this.utilsService.reloadCurrentRoute();
    }
  }

  filterNotTriggeredField(parent: any, field: any, answers: any) {
    let i;
    if (this.fieldUtilities.isFieldTriggered(parent, field, answers, this.score)) {
      for (i = 0; i < field.children.length; i++) {
        this.filterNotTriggeredField(field, field.children[i], answers);
      }
    }
  };

  preprocessTipAnswers(tip: any) {
    let x, i, j, k, step;

    for (let x = tip.questionnaires.length - 1; x >= 0; x--) {
      this.questionnaire = tip.questionnaires[x];
      this.fieldUtilities.parseQuestionnaire(this.questionnaire, {});

      for (i = 0; i < this.questionnaire.steps.length; i++) {
        step = this.questionnaire.steps[i];
        if (this.fieldUtilities.isFieldTriggered(null, step, this.questionnaire.answers, this.tip.score)) {
          for (j = 0; j < step.children.length; j++) {
            this.filterNotTriggeredField(step, step.children[j], this.questionnaire.answers);
          }
        }
      }

      for (i = 0; i < this.questionnaire.steps.length; i++) {
        step = this.questionnaire.steps[i];
        j = step.children.length;
        while (j--) {
          if (step.children[j]["template_id"] === "whistleblower_identity") {
            this.tip.whistleblower_identity_field = step.children[j];
            this.tip.whistleblower_identity_field.enabled = true;
            step.children.splice(j, 1);

            this.questionnaire = {
              steps: [{...this.tip.whistleblower_identity_field}]
            };

            this.tip.fields = this.questionnaire.steps[0].children;
            this.rows = this.fieldUtilities.splitRows(this.tip.fields);
            this.fieldUtilities.onAnswersUpdate(this);

            for (k = 0; k < this.tip.whistleblower_identity_field.children.length; k++) {
              this.filterNotTriggeredField(this.tip.whistleblower_identity_field, this.tip.whistleblower_identity_field.children[k], this.tip.data.whistleblower_identity);
            }
          }
        }
      }
    }
  }

  uploading() {
    return this.utilsService.isUploading(this.uploads);
  }

  calculateEstimatedTime() {
    let time = 0;
    for (const key in this.uploads) {
      if (this.uploads[key].flowFile && this.uploads[key].flowFile.isUploading()) {
        time = time + this.uploads[key].flowFile.timeRemaining();
      }
    }
    return time;
  }

  calculateProgress() {
    let progress = 0;
    let totalFiles = 0;
    for (const key in this.uploads) {
      if (this.uploads[key].flowFile) {
        progress = progress + this.uploads[key].flowFile.timeRemaining();
        totalFiles += 1;
      }
    }
    if (totalFiles === 0) {
      return 0;
    }

    return (100 - (progress / totalFiles) * 100);
  }

  provideIdentityInformation(_: { param1: string, param2: number }) {
    const intervalId = setInterval(() => {
      if (this.uploads) {
        for (const key in this.uploads) {

          if (this.uploads[key].flowFile && this.uploads[key].flowFile.isUploading()) {
            return;
          }
        }
      }

      this.httpService.whistleBlowerIdentityUpdate({
        "identity_field_id": this.tip.whistleblower_identity_field.id,
        "identity_field_answers": this.answers
      }).subscribe
      (
        {
          next: _ => {
            clearInterval(intervalId);
            this.onReload();
          },
          error: (_: any) => {
            clearInterval(intervalId);
            this.onReload();
          }
        }
      );

    }, 100);

  }

  onReload() {
    this.wbTipResolver.onReload(() => {
      this.utilsService.reloadCurrentRoute();
    });
  }

  onFormChange() {
    this.fieldUtilitiesService.onAnswersUpdate(this);
  }

}
