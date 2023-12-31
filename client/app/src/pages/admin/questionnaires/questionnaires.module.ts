import {NgModule} from "@angular/core";
import {CommonModule} from "@angular/common";

import {QuestionnairesRoutingModule} from "@app/pages/admin/questionnaires/questionnaires-routing.module";
import {QuestionnairesComponent} from "@app/pages/admin/questionnaires/questionnaires.component";
import {
  AddFieldFromTemplateComponent
} from "@app/pages/admin/questionnaires/add-field-from-template/add-field-from-template.component";
import {AddFieldComponent} from "@app/pages/admin/questionnaires/add-field/add-field.component";
import {FieldsComponent} from "@app/pages/admin/questionnaires/fields/fields.component";
import {MainComponent} from "@app/pages/admin/questionnaires/main/main.component";
import {QuestionsComponent} from "@app/pages/admin/questionnaires/questions/questions.component";
import {StepComponent} from "@app/pages/admin/questionnaires/step/step.component";
import {StepsComponent} from "@app/pages/admin/questionnaires/steps/steps.component";
import {FormsModule, ReactiveFormsModule} from "@angular/forms";
import {RouterModule} from "@angular/router";
import {
  NgbNavModule,
  NgbModule,
  NgbDropdownModule,
  NgbDatepickerModule,
  NgbDatepicker
} from "@ng-bootstrap/ng-bootstrap";
import {NgSelectModule} from "@ng-select/ng-select";
import {SharedModule} from "@app/shared.module";
import {StepsListComponent} from "@app/pages/admin/questionnaires/steps-list/steps-list.component";
import {
  QuestionnairesListComponent
} from "@app/pages/admin/questionnaires/questionnaires-list/questionnaires-list.component";
import {TranslateModule} from "@ngx-translate/core";
import {MarkdownModule} from "ngx-markdown";


@NgModule({
  declarations: [
    QuestionnairesComponent,
    AddFieldFromTemplateComponent,
    AddFieldComponent,
    FieldsComponent,
    MainComponent,
    QuestionsComponent,
    StepComponent,
    StepsComponent,
    StepsListComponent,
    QuestionnairesListComponent
  ],
  imports: [
    CommonModule,
    QuestionnairesRoutingModule, SharedModule, NgbNavModule, NgbModule, RouterModule, FormsModule, NgSelectModule,
    NgbDropdownModule,
    TranslateModule,
    MarkdownModule,
    ReactiveFormsModule, NgbDatepickerModule, NgbDatepicker

  ]
})
export class QuestionnairesModule {
}