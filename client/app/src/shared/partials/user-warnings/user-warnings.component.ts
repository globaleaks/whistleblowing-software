import {Component} from "@angular/core";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";

@Component({
  selector: "src-user-warnings",
  templateUrl: "./user-warnings.component.html"
})
export class UserWarningsComponent {

  constructor(protected authentication: AuthenticationService, protected preferenceResolver: PreferenceResolver, protected nodeResolver: NodeResolver) {
  }
}
