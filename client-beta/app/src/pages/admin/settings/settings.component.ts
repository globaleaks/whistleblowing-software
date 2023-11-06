import {Component, TemplateRef, ViewChild, AfterViewInit, ChangeDetectorRef} from "@angular/core";
import {NodeResolver} from "app/src/shared/resolvers/node.resolver";
import {AuthenticationService} from "@app/services/authentication.service";

@Component({
  selector: "src-settings",
  templateUrl: "./settings.component.html"
})
export class SettingsComponent implements AfterViewInit {
  @ViewChild("tab1") tab1!: TemplateRef<any>;
  @ViewChild("tab2") tab2!: TemplateRef<any>;
  @ViewChild("tab3") tab3!: TemplateRef<any>;
  @ViewChild("tab4") tab4!: TemplateRef<any>;
  @ViewChild("tab5") tab5!: TemplateRef<any>;
  tabs: any[];
  nodeData: any;
  active: string;

  constructor(protected node: NodeResolver, protected authenticationService: AuthenticationService, private cdr: ChangeDetectorRef) {

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
      ];
      if (this.authenticationService.session.role === "admin") {
        this.tabs = this.tabs.concat([
          {
            title: "Files",
            component: this.tab2
          },
          {
            title: "Languages",
            component: this.tab3
          },
          {
            title: "Text customization",
            component: this.tab4
          },
          {
            title: "Advanced",
            component: this.tab5
          }
        ]);
      }

      this.cdr.detectChanges();
    });
  }
}