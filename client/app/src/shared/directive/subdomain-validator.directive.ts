import {Directive, ElementRef, HostListener} from "@angular/core";
import {NgModel} from "@angular/forms";

@Directive({
  selector: "[subdomainvalidators]"
})
export class SubdomainValidatorDirective {

  @HostListener("input")
  onInput() {
    let viewValue: string = this.ngModel.value;
    viewValue = viewValue.toLowerCase();
    viewValue = viewValue.replace(/[^a-z0-9-]/g, "");
    this.el.nativeElement.value = viewValue;
    this.ngModel.update.emit(viewValue);
  }

  constructor(private el: ElementRef, private ngModel: NgModel) {
  }
}
