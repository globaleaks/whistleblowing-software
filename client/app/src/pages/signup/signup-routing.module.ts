import {NgModule} from "@angular/core";
import {RouterModule, Routes} from "@angular/router";
import {SignupComponent} from "@app/pages/signup/signup/signup.component";

const routes: Routes = [
  {
    path: "",
    component: SignupComponent,
    pathMatch: "full",
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class SignupRoutingModule {
}
