import {Component, TemplateRef, ViewChild} from "@angular/core";

@Component({
  selector: "src-settings",
  templateUrl: "./settings.component.html"
})
export class SettingsComponent {
  @ViewChild("tab1") tab1!: TemplateRef<any>;
  tabs: any[];
  nodeData: any;
  active: string;

  ngAfterViewInit(): void {
    this.active = "Settings";

    this.tabs = [
      {
        title: "Settings",
        component: this.tab1
      },
    ];
  }
}
