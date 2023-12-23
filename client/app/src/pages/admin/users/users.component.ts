import {AfterViewInit, Component, TemplateRef, ViewChild, ChangeDetectorRef} from "@angular/core";
import {Tab} from "@app/models/component-model/tab";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {UsersTab1Component} from "@app/pages/admin/users/users-tab1/users-tab1.component";
import {UsersTab2Component} from "@app/pages/admin/users/users-tab2/users-tab2.component";

@Component({
  selector: "src-users",
  templateUrl: "./users.component.html"
})
export class UsersComponent implements AfterViewInit {
  @ViewChild("tab1") tab1!: TemplateRef<UsersTab1Component>;
  @ViewChild("tab2") tab2!: TemplateRef<UsersTab2Component>;
  tabs: Tab[];
  nodeData: NodeResolver;
  active: string;

  constructor(public node: NodeResolver, private cdr: ChangeDetectorRef) {
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.active = "Users";

      this.nodeData = this.node;
      this.tabs = [
        {
          title: "Users",
          component: this.tab1
        },
        {
          title: "Options",
          component: this.tab2
        },
      ];

      this.cdr.detectChanges();
    });
  }
}