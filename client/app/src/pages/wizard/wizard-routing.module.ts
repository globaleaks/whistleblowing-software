import {NgModule} from "@angular/core";
import {RouterModule, Routes} from "@angular/router";
import {WizardComponent} from "@app/pages/wizard/wizard/wizard.component";

const routes: Routes = [
  {
    path: "",
    component: WizardComponent,
    pathMatch: "full",
  }

];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class WizardRoutingModule {
}
