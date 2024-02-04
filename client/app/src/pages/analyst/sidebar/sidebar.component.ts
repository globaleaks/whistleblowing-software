import {Component} from "@angular/core";
import {Router} from "@angular/router";

@Component({
  selector: "src-analyst-sidebar",
  templateUrl: "./sidebar.component.html"
})
export class SidebarComponent {
  constructor(private router: Router) {
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
