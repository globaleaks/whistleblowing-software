import {Component, TemplateRef, ViewChild, OnInit, AfterViewInit, ChangeDetectorRef} from "@angular/core";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {AuthenticationService} from "@app/services/authentication.service";

@Component({
  selector: "src-sites",
  templateUrl: "./sites.component.html"
})
export class SitesComponent implements OnInit, AfterViewInit {
  @ViewChild("tab1") tab1!: TemplateRef<any>;
  @ViewChild("tab2") tab2!: TemplateRef<any>;

  tabs: any[];
  nodeData: any;
  active: string;

  constructor(public node: NodeResolver, public authenticationService: AuthenticationService, private cdr: ChangeDetectorRef) {
  }

  ngOnInit() {
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.active = "Sites";

      this.nodeData = this.node;
      this.tabs = [
        {
          title: "Sites",
          component: this.tab1
        },
      ];
      if (this.authenticationService.session.role === "admin") {
        this.tabs = this.tabs.concat([
          {
            title: "Options",
            component: this.tab2
          }
        ]);
      }

      this.cdr.detectChanges();
    });
  }
}