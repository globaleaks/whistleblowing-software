import {TemplateRef} from "@angular/core";

export interface Tab {
  title: string;
  component: TemplateRef<any>;
}