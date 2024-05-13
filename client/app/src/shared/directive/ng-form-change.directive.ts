import {Directive, EventEmitter, OnDestroy, OnInit, Output} from "@angular/core";
import {debounceTime, Subscription} from "rxjs";
import {NgForm} from "@angular/forms";

@Directive({
  selector: "[ngFormChanges]"
})
export class NgFormChangeDirective implements OnInit, OnDestroy {

  @Output("ngFormChange") formChange: EventEmitter<any> = new EventEmitter<any>();
  private formSubscription: Subscription;

  constructor(private ngForm: NgForm) {
  }

  ngOnInit() {
    this.formSubscription = this.ngForm.form.valueChanges.pipe(debounceTime(150)).subscribe(() => {
      this.formChange.emit();
    });
  }

  ngOnDestroy() {
    this.formSubscription.unsubscribe();
  }
}
