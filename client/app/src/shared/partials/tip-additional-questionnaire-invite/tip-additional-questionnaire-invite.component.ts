import {Component} from "@angular/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {
  TipAdditionalQuestionnaireFormComponent
} from "@app/shared/modals/tip-additional-questionnaire-form/tip-additional-questionnaire-form.component";

@Component({
  selector: "src-tip-additional-questionnaire-invite",
  templateUrl: "./tip-additional-questionnaire-invite.component.html"
})
export class TipAdditionalQuestionnaireInviteComponent {
  collapsed = false;

  public toggleColLapse() {
    this.collapsed = !this.collapsed;
  }

  constructor(protected utilsService: UtilsService, private modalService: NgbModal) {
  }

  tipOpenAdditionalQuestionnaire() {
    this.modalService.open(TipAdditionalQuestionnaireFormComponent, {
      windowClass: "custom-modal-width",
      backdrop: 'static',
      keyboard: false
    });
  }
}
