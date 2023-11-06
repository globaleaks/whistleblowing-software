import {Component, TemplateRef, ViewChild, AfterViewInit, ChangeDetectorRef} from "@angular/core";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";

@Component({
  selector: "src-casemanagement",
  templateUrl: "./case-management.component.html"
})
export class CaseManagementComponent implements AfterViewInit {
  @ViewChild("tab1") tab1!: TemplateRef<any>;
  tabs: any[];
  nodeData: any;
  active: string;

  constructor(protected node: NodeResolver, private cdr: ChangeDetectorRef) {
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.active = "Report statuses";

      this.nodeData = this.node;
      this.tabs = [
        {
          title: "Report statuses",
          component: this.tab1
        },
      ];

      this.cdr.detectChanges();
    });
  }
}
