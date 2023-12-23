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

  hasMultipleEntries(field_answer: any) {
    return field_answer.length > 1;
  };
}
