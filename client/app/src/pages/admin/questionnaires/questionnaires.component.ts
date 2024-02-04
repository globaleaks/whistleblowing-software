import {Component, TemplateRef, ViewChild, AfterViewInit, ChangeDetectorRef} from "@angular/core";
import {Tab} from "@app/models/component-model/tab";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {MainComponent} from "@app/pages/admin/questionnaires/main/main.component";
import {QuestionsComponent} from "@app/pages/admin/questionnaires/questions/questions.component";

@Component({
  selector: "src-questionnaires",
  templateUrl: "./questionnaires.component.html"
})
export class QuestionnairesComponent implements AfterViewInit {
  @ViewChild("tab1") tab1!: TemplateRef<MainComponent>;
  @ViewChild("tab2") tab2!: TemplateRef<QuestionsComponent>;
  tabs: Tab[];
  nodeData: NodeResolver;
  active: string;

  constructor(protected node: NodeResolver, private cdr: ChangeDetectorRef) {
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.active = "Questionnaires";

      this.nodeData = this.node;
      this.tabs = [
        {
          title: "Questionnaires",
          component: this.tab1
        },
        {
          title: "Question templates",
          component: this.tab2
        },
      ];

      this.cdr.detectChanges();
    });
  }
}