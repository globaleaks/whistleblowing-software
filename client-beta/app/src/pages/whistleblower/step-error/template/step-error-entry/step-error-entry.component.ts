import {Component, Input, OnInit} from "@angular/core";
import {NgForm} from "@angular/forms";

@Component({
  selector: "src-step-error-entry",
  templateUrl: "./step-error-entry.component.html"
})
export class StepErrorEntryComponent implements OnInit {
  @Input() navigation: any;
  @Input() err: any;
  @Input() field_id_map: any;
  @Input() form!: NgForm;
  pre = "fieldForm_";
  f_id: any;
  field: any;

  ngOnInit(): void {
    this.initialize();
  }

  goToQuestion() {
    const form = document.getElementById(this.err);

    if (form) {
      form.scrollIntoView({behavior: "smooth", block: "start"});
      const offset = 35;
      const elementTop = form.getBoundingClientRect().top - window.pageYOffset;
      const scrollToPosition = elementTop - offset;
      window.scrollTo({top: scrollToPosition, behavior: "smooth"});
    }
  }

  initialize() {
    this.f_id = this.err;
    this.f_id = this.f_id.substring(0, this.f_id.indexOf("$"));
    this.f_id = this.f_id.slice(this.pre.length).replace(new RegExp("_", "g"), "-");
    this.field = this.field_id_map[this.f_id];
  }
}
