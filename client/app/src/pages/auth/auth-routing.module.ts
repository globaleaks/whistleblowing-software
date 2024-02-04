import {NgModule} from "@angular/core";
import {RouterModule, Routes} from "@angular/router";
import {LoginComponent} from "@app/pages/auth/login/login.component";
import {PasswordResetComponent} from "@app/pages/auth/password-reset/password-reset.component";
import {PasswordRequestedComponent} from "@app/pages/auth/passwordreqested/password-requested.component";

const routes: Routes = [
  {
    path: "",
    component: LoginComponent,
    pathMatch: "full",
    data: {pageTitle: "Log in"},
  },
  {
    path: "passwordreset",
    component: PasswordResetComponent,
    pathMatch: "full",
    data: {pageTitle: "Password reset"},
  },
  {
    path: "passwordreset/requested",
    component: PasswordRequestedComponent,
    pathMatch: "full",
    data: {pageTitle: "Password reset"},
  }

];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AuthRoutingModule {
}
