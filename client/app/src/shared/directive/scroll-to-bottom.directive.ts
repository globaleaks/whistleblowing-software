import {Directive, ElementRef} from "@angular/core";

@Directive({
  selector: "[scroll-to-bottom]"
})
export class ScrollToBottomDirective {
  constructor(private elementRef: ElementRef) {
  }

  public scrollToBottom() {
    const el: HTMLDivElement = this.elementRef.nativeElement;
    el.scrollTop = Math.max(0, el.scrollHeight - el.offsetHeight);
  }
}