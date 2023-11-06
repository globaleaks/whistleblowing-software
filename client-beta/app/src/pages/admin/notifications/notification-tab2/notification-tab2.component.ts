import {Component, Input, OnInit} from "@angular/core";
import {NgForm} from "@angular/forms";
import {NotificationsResolver} from "@app/shared/resolvers/notifications.resolver";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-notification-tab2",
  templateUrl: "./notification-tab2.component.html"
})
export class NotificationTab2Component implements OnInit {
  @Input() notificationForm: NgForm;
  template: any;
  notificationData: any = [];

  constructor(private notificationResolver: NotificationsResolver, private utilsService: UtilsService) {
  }

  ngOnInit(): void {
    this.notificationData = this.notificationResolver.dataModel;
  }

  updateNotification(notification: any) {
    this.utilsService.updateAdminNotification(notification).subscribe();
  }
}