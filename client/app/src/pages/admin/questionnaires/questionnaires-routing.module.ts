import {NgModule} from "@angular/core";
import {RouterModule, Routes} from "@angular/router";
import {QuestionnairesComponent} from "@app/pages/admin/questionnaires/questionnaires.component";

const routes: Routes = [
  {
    path: "",
    component: QuestionnairesComponent,
    pathMatch: "full",
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class QuestionnairesRoutingModule {
}