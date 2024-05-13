import {Component, Input, OnInit} from "@angular/core";
import {NgForm} from "@angular/forms";
import {notificationResolverModel} from "@app/models/resolvers/notification-resolver-model";
import {NotificationsResolver} from "@app/shared/resolvers/notifications.resolver";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-notification-tab2",
  templateUrl: "./notification-tab2.component.html"
})
export class NotificationTab2Component implements OnInit {
  @Input() notificationForm: NgForm;
  template: string;
  notificationData: notificationResolverModel;

  constructor(private notificationResolver: NotificationsResolver, private utilsService: UtilsService) {
  }

  ngOnInit(): void {
    this.notificationData = this.notificationResolver.dataModel;
  }

  updateNotification(notification: notificationResolverModel) {
    this.utilsService.updateAdminNotification(notification).subscribe();
  }
}