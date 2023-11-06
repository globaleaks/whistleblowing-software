import {NgModule} from "@angular/core";
import {AuthRoutingModule} from "@app/pages/auth/auth-routing.module";
import {AdminRoutingModule} from "@app/pages/admin/admin-routing.module";
import {RouterModule, Routes} from "@angular/router";
import {SessionGuard} from "@app/app-guard.service";
import {HomeComponent} from "@app/pages/dashboard/home/home.component";
import {PasswordResetResponseComponent} from "@app/pages/auth/password-reset-response/password-reset-response.component";
import {RecipientRoutingModule} from "@app/pages/recipient/recipient-routing.module";
import {AdminGuard} from "@app/shared/guards/admin.guard";
import {CustodianGuard} from "@app/shared/guards/custodian.guard";
import {ReceiverGuard} from "@app/shared/guards/receiver.guard";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {ActionRoutingModule} from "@app/pages/action/action-routing.module";
import {SignupRoutingModule} from "@app/pages/signup/signup-routing.module";
import {Pageguard} from "@app/shared/guards/pageguard.service";
import {ActivationComponent} from "@app/pages/signup/templates/activation/activation.component";
import {WizardRoutingModule} from "@app/pages/wizard/wizard-routing.module";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {RTipsResolver} from "@app/shared/resolvers/r-tips-resolver.service";
import {TipComponent} from "@app/pages/recipient/tip/tip.component";
import {TitleResolver} from "@app/shared/resolvers/title-resolver.resolver";
import {CustodianRoutingModule} from "@app/pages/custodian/custodian-routing.module";
import {IarResolver} from "@app/shared/resolvers/iar-resolver.service";
import {BlankComponent} from "@app/shared/blank/blank.component";
import {WbTipResolver} from "@app/shared/resolvers/wb-tip-resolver.service";
import {WhistleblowerLoginResolver} from "@app/shared/resolvers/whistleblower-login.resolver";


const routes: Routes = [
  {
    path: "blank",
    pathMatch: "full",
    component: BlankComponent
  },
  {
    path: "",
    canActivate: [Pageguard],
    component: HomeComponent,
    data: {pageTitle: ""},
    pathMatch: "full",
    resolve: {
      WbTipResolver, WhistleblowerLoginResolver
    }
  },
  {
    path: "login",
    data: {pageTitle: "Log in"},
    loadChildren: () => AuthRoutingModule,
  },
  {
    path: "signup",
    data: {pageTitle: "Sign up"},
    resolve: {
      PreferenceResolver
    },
    loadChildren: () => SignupRoutingModule,

  },
  {
    path: "action",
    loadChildren: () => ActionRoutingModule,
  },
  {
    path: "recipient",
    canActivate: [ReceiverGuard],
    resolve: {
      PreferenceResolver, RTipsResolver
    },
    loadChildren: () => RecipientRoutingModule,
    data: {
      sidebar: "recipient-sidebar"
    }
  },
  {
    path: "custodian",
    canActivate: [CustodianGuard],
    resolve: {
      PreferenceResolver, NodeResolver, RtipsResolver: RTipsResolver, IarsResolver: IarResolver
    },
    loadChildren: () => CustodianRoutingModule,
    data: {
      sidebar: "custodian-sidebar", pageTitle: "Home"
    },
  },
  {
    path: "admin",
    canActivate: [AdminGuard],
    loadChildren: () => AdminRoutingModule,
    data: {
      sidebar: "admin-sidebar", pageTitle: "Log in"
    },
  },
  {
    path: "password/reset",
    data: {pageTitle: "Password reset"},
    component: PasswordResetResponseComponent,
  },
  {
    path: "activation",
    data: {pageTitle: "Sign up"},
    component: ActivationComponent,
  },
  {
    path: "wizard",
    data: {pageTitle: "Platform wizard"},
    resolve: {
      PreferenceResolver,
      title: TitleResolver
    },
    loadChildren: () => WizardRoutingModule,
  },
  {
    path: "status/:tip_id",
    data: {pageTitle: "Report"},
    component: TipComponent,
    canActivate: [SessionGuard],
    pathMatch: "full",
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {

}
