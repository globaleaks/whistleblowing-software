import {Component, OnInit, QueryList, ViewChild, ViewChildren} from "@angular/core";
import {WbTipResolver} from "@app/shared/resolvers/wb-tip-resolver.service";
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";
import {NgForm} from "@angular/forms";
import {WbtipService} from "@app/services/wbtip.service";
import {FieldUtilitiesService} from "@app/shared/services/field-utilities.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {HttpService} from "@app/shared/services/http.service";

@Component({
  selector: "src-tip-additional-questionnaire-form",
  templateUrl: "./tip-additional-questionnaire-form.component.html"
})
export class TipAdditionalQuestionnaireFormComponent implements OnInit {

  @ViewChild("submissionForm") public submissionForm: NgForm;
  @ViewChildren("stepform") stepForms: QueryList<NgForm>;

  validate: any = {};
  navigation = 0;
  score = 0;
  questionnaire: any;
  answers: any = {};
  field_id_map: any;
  done: boolean = false;
  uploads: any = {};
  file_upload_url = "api/whistleblower/wbtip/rfile";

  constructor(private wbTipResolver: WbTipResolver, private httpService: HttpService, private fieldUtilitiesService: FieldUtilitiesService, private utilsService: UtilsService, protected wbTipService: WbtipService, protected activeModal: NgbActiveModal) {
  }

  ngOnInit(): void {
    this.prepareSubmission();
  }

  goToStep(step: number) {
    this.navigation = step;
    this.utilsService.scrollToTop();
  }

  firstStepIndex() {
    return 0;
  };

  lastStepIndex() {
    let last_enabled = 0;

    for (let i = 0; i < this.questionnaire.steps.length; i++) {
      if (this.questionnaire.steps[i].enabled) {
        last_enabled = i;
      }
    }

    return last_enabled;
  };

  uploading() {
    let uploading = false;
    if (this.uploads && this.done) {
      for (const key in this.uploads) {
        if (this.uploads[key].flowJs && this.uploads[key].flowJs.isUploading()) {
          uploading = true;
        }
      }
    }

    return uploading;
  }

  calculateEstimatedTime() {
    let timeRemaining = 0;
    if (this.uploads && this.done) {
      for (const key in this.uploads) {
        if (this.uploads[key] && this.uploads[key].flowJs) {
          timeRemaining += this.uploads[key].flowJs.timeRemaining();
        }
      }
    }

    return timeRemaining;
  }

  calculateProgress() {
    let progress = 0;
    if (this.uploads && this.done) {
      for (const key in this.uploads) {
        if (this.uploads[key] && this.uploads[key].flowJs) {
          progress += this.uploads[key].flowJs.progress();
        }
      }
    }

    return progress;
  }

  hasNextStep() {
    return this.navigation < this.lastStepIndex();
  };

  hasPreviousStep() {
    return this.navigation > this.firstStepIndex();
  };

  checkForInvalidFields() {
    for (let counter = 0; counter <= this.navigation; counter++) {
      this.validate[counter] = true;
      if (this.questionnaire.steps[counter].enabled) {
        if (this.stepForms.get(counter)?.invalid) {
          this.navigation = counter;
          return false;
        }
      }
    }
    return true;
  }

  runValidation() {
    this.validate[this.navigation] = true;

    if (this.navigation > -1 && !this.checkForInvalidFields()) {
      this.utilsService.scrollToTop();
      return false;
    }

    return true;
  };

  incrementStep() {
    if (!this.runValidation()) {
      return;
    }

    if (this.hasNextStep()) {
      for (let i = this.navigation + 1; i <= this.lastStepIndex(); i++) {
        if (this.fieldUtilitiesService.isFieldTriggered(null, this.questionnaire.steps[i], this.answers, this.score)) {
          this.navigation = i;
          this.utilsService.scrollToTop();
          return;
        }
      }
    }
  }

  decrementStep() {
    if (this.hasPreviousStep()) {
      for (let i = this.navigation - 1; i >= this.firstStepIndex(); i--) {
        if (i === -1 || this.fieldUtilitiesService.isFieldTriggered(null, this.questionnaire.steps[i], this.answers, this.score)) {
          this.navigation = i;
          this.utilsService.scrollToTop();
          return;
        }
      }
    }
  };

  areReceiversSelected() {
    return true;
  };

  prepareSubmission() {
    this.done = false;
    this.answers = {};
    this.uploads = {};
    this.questionnaire = this.wbTipService.tip.additional_questionnaire;
    this.fieldUtilitiesService.onAnswersUpdate(this);
    this.field_id_map = this.fieldUtilitiesService.build_field_id_map(this.questionnaire);
  };

  completeSubmission() {
    this.fieldUtilitiesService.onAnswersUpdate(this);

    if (!this.runValidation()) {
      this.utilsService.scrollToTop();
      return;
    }

    this.done = true;
    this.utilsService.resumeFileUploads(this.uploads);

    const intervalId = setInterval(() => {
      if (this.uploads) {
        for (const key in this.uploads) {
          if (this.uploads[key].flowFile && this.uploads[key].flowFile.isUploading()) {
            return;
          }
        }
      }
      this.fieldUtilitiesService.onAnswersUpdate(this);

      if (this.uploading()) {
        return;
      }

      this.httpService.whistleBlowerTipUpdate({
        "cmd": "additional_questionnaire",
        "answers": this.answers
      }).subscribe
      (
        {
          next: _ => {
            this.wbTipResolver.onReload(() => {
              this.utilsService.reloadCurrentRoute();
            });
          }
        }
      );

      clearInterval(intervalId);
      this.activeModal.dismiss();
    }, 1000);
  }

  stepForm(index: any): any {
    if (this.stepForms && index !== -1) {
      return this.stepForms.get(index);
    }
  };

  displayStepErrors(index: number): any {
    if (index !== -1) {
      const response = this.stepForm(index);
      if (response) {
        return response?.invalid;
      } else {
        return false;
      }
    }
  };

  displayErrors() {
    if (!(this.validate[this.navigation])) {
      return false;
    }

    return !!this.displayStepErrors(this.navigation);
  };

  onFormChange() {
    this.fieldUtilitiesService.onAnswersUpdate(this);
  }

  onFileUpload(upload: any) {
    if (upload) {
      this.uploads = upload;
      this.fieldUtilitiesService.onAnswersUpdate(this);
    }
  }
}