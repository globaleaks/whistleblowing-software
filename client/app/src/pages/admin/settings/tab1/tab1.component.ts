import {Component, Input} from "@angular/core";
import {ControlContainer, NgForm} from "@angular/forms";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {UtilsService} from "@app/shared/services/utils.service";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {AppConfigService} from "@app/services/root/app-config.service";
import {Constants} from "@app/shared/constants/constants";
import {AppDataService} from "@app/app-data.service";

@Component({
  selector: "src-tab1",
  templateUrl: "./tab1.component.html",
  viewProviders: [{provide: ControlContainer, useExisting: NgForm}],
})
export class Tab1Component {
  protected readonly Constants = Constants;
  @Input() contentForm: NgForm;

  constructor(private appConfigService: AppConfigService, protected nodeResolver: NodeResolver,protected appDataService:AppDataService, protected authenticationService: AuthenticationService, private utilsService: UtilsService) {
  }

  updateNode() {
    this.utilsService.update(this.nodeResolver.dataModel).subscribe(_ => {
      this.appConfigService.reinit(false);
      this.utilsService.reloadComponent();
    });
  }
}