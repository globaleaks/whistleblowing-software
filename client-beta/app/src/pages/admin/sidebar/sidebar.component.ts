import {ChangeDetectionStrategy, Component} from "@angular/core";
import { Router } from "@angular/router";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";

@Component({
  selector: "src-admin-sidebar",
  templateUrl: "./sidebar.component.html",
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SidebarComponent {

  constructor(private router: Router, protected nodeResolver: NodeResolver) {
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