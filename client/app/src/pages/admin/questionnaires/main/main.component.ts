import {HttpClient} from "@angular/common/http";
import {ChangeDetectorRef, Component, ElementRef, OnDestroy, OnInit, ViewChild} from "@angular/core";
import {questionnaireResolverModel} from "@app/models/resolvers/questionnaire-model";
import {QuestionnairesResolver} from "@app/shared/resolvers/questionnaires.resolver";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {NewQuestionare} from "@app/models/admin/new-questionare";
import {QuestionnaireService} from "@app/pages/admin/questionnaires/questionnaire.service";
import {Subject, takeUntil} from "rxjs";

@Component({
  selector: "src-main",
  templateUrl: "./main.component.html"
})
export class MainComponent implements OnInit, OnDestroy {

  private destroy$ = new Subject<void>();
  questionnairesData: questionnaireResolverModel[] = [];
  new_questionnaire: { name: string } = {name: ""};
  showAddQuestionnaire: boolean = false;
  @ViewChild('keyUploadInput') keyUploadInput: ElementRef<HTMLInputElement>;

  constructor(private http: HttpClient, private questionnaireService: QuestionnaireService, private httpService: HttpService, private utilsService: UtilsService, private cdr: ChangeDetectorRef, protected questionnairesResolver: QuestionnairesResolver) {
  }

  ngOnInit(): void {
    this.questionnaireService.sharedData = "step";
    this.questionnaireService.getData().pipe(takeUntil(this.destroy$)).subscribe(() => {
      return this.getResolver();
    });
    this.questionnairesData = this.questionnairesResolver.dataModel;
    this.cdr.markForCheck();
  }

  addQuestionnaire() {
    const questionnaire: NewQuestionare = new NewQuestionare();
    questionnaire.name = this.new_questionnaire.name;
    this.httpService.addQuestionnaire(questionnaire).subscribe(res => {
      this.questionnairesData.push(res);
      this.new_questionnaire = {name: ""};
      this.getResolver();
      this.cdr.markForCheck();
    });
  }

  toggleAddQuestionnaire(): void {
    this.showAddQuestionnaire = !this.showAddQuestionnaire;
  }

  importQuestionnaire(files: FileList | null) {
    if (files && files.length > 0) {
      this.utilsService.readFileAsText(files[0]).subscribe((txt) => {
        return this.http.post("api/admin/questionnaires?multilang=1", txt).subscribe({
          next:()=>{
            this.getResolver();
          },
          error:()=>{
            if (this.keyUploadInput) {
                this.keyUploadInput.nativeElement.value = "";
            }
          }
        });
      });
    }
  }

  getResolver() {
    return this.httpService.requestQuestionnairesResource().subscribe((response: questionnaireResolverModel[]) => {
      this.questionnairesResolver.dataModel = response;
      this.questionnairesData = response;
      this.cdr.markForCheck();
    });
  }

  trackByFn(_: number, item: questionnaireResolverModel) {
    return item.id;
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }
}