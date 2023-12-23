import {NgModule} from "@angular/core";
import {RouterModule, Routes} from "@angular/router";
import {NotificationsComponent} from "@app/pages/admin/notifications/notifications.component";

const routes: Routes = [
  {
    path: "",
    component: NotificationsComponent,
    pathMatch: "full",
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class NotificationsRoutingModule {
}