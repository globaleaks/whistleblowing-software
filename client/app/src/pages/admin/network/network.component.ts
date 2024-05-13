import {Component, TemplateRef, ViewChild, AfterViewInit, ChangeDetectorRef} from "@angular/core";
import {Tab} from "@app/models/component-model/tab";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {HttpsComponent} from "@app/pages/admin/network/https/https.component";
import {TorComponent} from "@app/pages/admin/network/tor/tor.component";
import {AccessControlComponent} from "@app/pages/admin/network/access-control/access-control.component";
import {UrlRedirectsComponent} from "@app/pages/admin/network/url-redirects/url-redirects.component";

@Component({
  selector: "src-network",
  templateUrl: "./network.component.html"
})
export class NetworkComponent implements AfterViewInit {
  @ViewChild("tab1") tab1!: TemplateRef<HttpsComponent>;
  @ViewChild("tab2") tab2!: TemplateRef<TorComponent>;
  @ViewChild("tab3") tab3!: TemplateRef<AccessControlComponent>;
  @ViewChild("tab4") tab4!: TemplateRef<UrlRedirectsComponent>;

  tabs: Tab[];
  nodeData: NodeResolver;
  active: string;

  constructor(
    public node: NodeResolver,
    private cdr: ChangeDetectorRef
  ) {
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.active = "HTTPS";

      this.nodeData = this.node;
      this.tabs = [
        {
          id:"https",
          title: "HTTPS",
          component: this.tab1
        },
        {
          id:"tor",
          title: "Tor",
          component: this.tab2
        },
        {
          id:"access_control",
          title: "Access control",
          component: this.tab3
        },
        {
          id:"url_redirects",
          title: "URL redirects",
          component: this.tab4
        },
      ];

      this.cdr.detectChanges();
    });
  }
}