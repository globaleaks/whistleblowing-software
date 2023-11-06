import {AfterViewInit, Component, TemplateRef, ViewChild, ChangeDetectorRef} from "@angular/core";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {AuthenticationService} from "@app/services/authentication.service";

@Component({
  selector: "src-auditlog",
  templateUrl: "./audit-log.component.html"
})
export class AuditLogComponent implements AfterViewInit {
  @ViewChild("tab1") tab1!: TemplateRef<any>;
  @ViewChild("tab2") tab2!: TemplateRef<any>;
  @ViewChild("tab3") tab3!: TemplateRef<any>;
  @ViewChild("tab4") tab4!: TemplateRef<any>;

  tabs: any[];
  nodeData: any;
  active: string;

  constructor(private nodeResolver: NodeResolver, private authenticationService: AuthenticationService, private cdr: ChangeDetectorRef) {
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.active = "Audit Log";

      this.nodeData = this.nodeResolver;
      this.tabs = [
        {
          title: "Audit Log",
          component: this.tab1
        },
      ];
      if (this.authenticationService.session.role === "admin") {
        this.tabs = this.tabs.concat([
          {
            title: "Users",
            component: this.tab2
          },
          {
            title: "Reports",
            component: this.tab3
          },
          {
            title: "Scheduled jobs",
            component: this.tab4
          }
        ]);
      }

      this.cdr.detectChanges();
    });
  }
}
