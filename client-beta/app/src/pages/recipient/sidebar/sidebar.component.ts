import {Component} from "@angular/core";
import { Router } from "@angular/router";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";

@Component({
  selector: "src-receipt-sidebar",
  templateUrl: "./sidebar.component.html"
})
export class SidebarComponent {
  message: string;

  constructor(private router: Router, protected preferenceResolver: PreferenceResolver) {
  }

  isActive(route: string): boolean {
    return this.router.isActive(route, {
      paths: "subset",
      queryParams: "subset",
      fragment: "ignored",
      matrixParams: "ignored"
    });
  }
}
