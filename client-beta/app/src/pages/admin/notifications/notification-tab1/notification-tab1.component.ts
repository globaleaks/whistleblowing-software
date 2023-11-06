import {Component, Input} from "@angular/core";
import {NgForm} from "@angular/forms";
import {Constants} from "@app/shared/constants/constants";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {NotificationsResolver} from "@app/shared/resolvers/notifications.resolver";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-notification-tab1",
  templateUrl: "./notification-tab1.component.html"
})
export class NotificationTab1Component {
  @Input() notificationForm: NgForm;
  protected readonly Constants = Constants;

  constructor(protected nodeResolver: NodeResolver, protected notificationResolver: NotificationsResolver, private utilsService: UtilsService) {
  }

  updateNotification(notification: any) {
    this.utilsService.updateAdminNotification(notification).subscribe(_ => {
      this.utilsService.reloadCurrentRoute();
    });
  }

  updateThenTestMail(notification: any): void {
    this.utilsService.updateAdminNotification(notification).subscribe(() => this.utilsService.runAdminOperation("test_mail", {}, true));
  }

  resetSMTPSettings() {
    this.utilsService.runAdminOperation("reset_smtp_settings", {}, true);
  }

  resetTemplates() {
    this.utilsService.runAdminOperation("reset_templates", {}, true);
  }
}