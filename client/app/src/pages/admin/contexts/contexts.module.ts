import {NgModule} from "@angular/core";
import {CommonModule} from "@angular/common";
import {ContextsRoutingModule} from "@app/pages/admin/contexts/contexts-routing.module";
import {ContextsComponent} from "@app/pages/admin/contexts/contexts.component";
import {FormsModule} from "@angular/forms";
import {RouterModule} from "@angular/router";
import {NgbNavModule, NgbModule} from "@ng-bootstrap/ng-bootstrap";
import {NgSelectModule} from "@ng-select/ng-select";
import {SharedModule} from "@app/shared.module";
import {ContextEditorComponent} from "@app/pages/admin/contexts/context-editor/context-editor.component";


@NgModule({
  declarations: [
    ContextsComponent,
    ContextEditorComponent
  ],
  imports: [
    CommonModule,
    ContextsRoutingModule, SharedModule, NgbNavModule, NgbModule, RouterModule, FormsModule, NgSelectModule
  ]
})
export class ContextsModule {
}
