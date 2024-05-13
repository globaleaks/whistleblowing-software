import {NgModule} from "@angular/core";
import {CommonModule} from "@angular/common";
import {ForcedTwoFactorComponent} from "@app/pages/action/forced-two-factor/forced-two-factor.component";
import {SharedModule} from "@app/shared.module";
import {TranslateModule} from "@ngx-translate/core";
import {ForcePasswordChangeComponent} from "@app/pages/action/force-password-change/force-password-change.component";
import {FormsModule, ReactiveFormsModule} from "@angular/forms";


@NgModule({
  declarations: [
    ForcedTwoFactorComponent,
    ForcePasswordChangeComponent
  ],
  imports: [
    CommonModule,
    TranslateModule,
    FormsModule,
    ReactiveFormsModule,
    SharedModule
  ]
})
export class ActionModule {
}