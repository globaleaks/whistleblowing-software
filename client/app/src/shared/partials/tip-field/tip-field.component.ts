import {Component, Input} from "@angular/core";

@Component({
  selector: "src-tip-field",
  templateUrl: "./tip-field.component.html"
})
export class TipFieldComponent {
  @Input() fields: any;
  @Input() index: number;
  @Input() fieldAnswers: any;
  @Input() preview: boolean = false;
  @Input() redactMode: boolean;
  @Input() redactOperationTitle: string;

  hasMultipleEntries(field_answer: any): boolean {
    return Array.isArray(field_answer) && field_answer.length > 1;
  };
}
