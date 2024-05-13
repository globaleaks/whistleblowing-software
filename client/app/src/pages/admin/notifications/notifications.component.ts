import {Component, TemplateRef, ViewChild, AfterViewInit, ChangeDetectorRef} from "@angular/core";
import {Tab} from "@app/models/component-model/tab";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {NotificationTab1Component} from "@app/pages/admin/notifications/notification-tab1/notification-tab1.component";
import {NotificationTab2Component} from "@app/pages/admin/notifications/notification-tab2/notification-tab2.component";

@Component({
  selector: "src-notifications",
  templateUrl: "./notifications.component.html"
})
export class NotificationsComponent implements AfterViewInit {
  @ViewChild("tab1") tab1!: TemplateRef<NotificationTab1Component>;
  @ViewChild("tab2") tab2!: TemplateRef<NotificationTab2Component>;

  tabs: Tab[];
  nodeData: NodeResolver;
  active: string;

  constructor(protected node: NodeResolver, private cdr: ChangeDetectorRef) {
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.active = "Settings";

      this.nodeData = this.node;
      this.tabs = [
        {
          id:"settings",
          title: "Settings",
          component: this.tab1
        },
        {
          id:"templates",
          title: "Templates",
          component: this.tab2
        },
      ];

      this.cdr.detectChanges();
    });
  }
}