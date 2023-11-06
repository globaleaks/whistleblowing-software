import {Component, TemplateRef, ViewChild, AfterViewInit, ChangeDetectorRef} from "@angular/core";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";

@Component({
  selector: "src-notifications",
  templateUrl: "./notifications.component.html"
})
export class NotificationsComponent implements AfterViewInit {
  @ViewChild("tab1") tab1!: TemplateRef<any>;
  @ViewChild("tab2") tab2!: TemplateRef<any>;

  tabs: any[];
  nodeData: any;
  active: string;

  constructor(protected node: NodeResolver, private cdr: ChangeDetectorRef) {
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.active = "Settings";

      this.nodeData = this.node;
      this.tabs = [
        {
          title: "Settings",
          component: this.tab1
        },
        {
          title: "Templates",
          component: this.tab2
        },
      ];

      this.cdr.detectChanges();
    });
  }
}