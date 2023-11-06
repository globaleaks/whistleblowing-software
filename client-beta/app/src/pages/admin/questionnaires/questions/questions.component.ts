import {HttpClient} from "@angular/common/http";
import {Component, OnDestroy, OnInit} from "@angular/core";
import {FieldTemplatesResolver} from "@app/shared/resolvers/field-templates-resolver.service";
import {QuestionnairesResolver} from "@app/shared/resolvers/questionnaires.resolver";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {QuestionnaireService} from "@app/pages/admin/questionnaires/questionnaire.service";
import {Subject, takeUntil} from "rxjs";

@Component({
  selector: "src-questions",
  templateUrl: "./questions.component.html"
})
export class QuestionsComponent implements OnInit, OnDestroy {
  showAddQuestion: boolean = false;
  fields: any;
  questionnairesData: any = [];
  step: any;

  private destroy$ = new Subject<void>();

  constructor(private questionnaireService: QuestionnaireService, private httpClient: HttpClient, private httpService: HttpService, private utilsService: UtilsService, private fieldTemplates: FieldTemplatesResolver, private questionnairesResolver: QuestionnairesResolver) {
  }

  ngOnInit(): void {
    this.questionnaireService.getQuestionnairesData().pipe(takeUntil(this.destroy$)).subscribe(() => {
      this.getResolver();
      return this.getQuestionnairesResolver();
    });
    this.questionnairesData = this.questionnairesResolver.dataModel;
    this.fields = this.fieldTemplates.dataModel;
    this.fields = this.fields.filter((field: { editable: boolean; }) => field.editable);
  }

  toggleAddQuestion() {
    this.showAddQuestion = !this.showAddQuestion;
  };

  importQuestion(file: any): void {
    this.utilsService.readFileAsText(file[0]).then((txt) => {
      return this.httpClient.post("api/admin/fieldtemplates?multilang=1", txt).subscribe(() => {
        this.utilsService.reloadCurrentRoute();
      });
    });
  }

  getQuestionnairesResolver() {
    return this.httpService.requestQuestionnairesResource().subscribe(response => {
      this.questionnairesResolver.dataModel = response;
      this.questionnairesData = response;
    });
  }

  getResolver() {
    return this.httpService.requestAdminFieldTemplateResource().subscribe(response => {
      this.fieldTemplates.dataModel = response;
      this.fields = response;
      this.fields = this.fields.filter((field: { editable: boolean; }) => field.editable);
    });
  }

  listenToAddField() {
    this.showAddQuestion = false;
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }
}