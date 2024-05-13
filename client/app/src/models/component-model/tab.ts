import {TemplateRef} from "@angular/core";

export interface Tab {
  id?:string
  title: string;
  component: TemplateRef<any>;
}