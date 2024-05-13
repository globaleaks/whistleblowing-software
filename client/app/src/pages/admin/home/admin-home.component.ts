import {Component, OnInit} from "@angular/core";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {nodeResolverModel} from "@app/models/resolvers/node-resolver-model";
import {preferenceResolverModel} from "@app/models/resolvers/preference-resolver-model";
import { UtilsService } from "@app/shared/services/utils.service";

@Component({
  selector: "src-admin-home",
  templateUrl: "./admin-home.component.html"
})
export class adminHomeComponent implements OnInit {
  active: number = 0;
  nodeData: nodeResolverModel;
  preferenceData: preferenceResolverModel;

  constructor(private utilsService: UtilsService, private preference: PreferenceResolver, protected nodeResolver: NodeResolver) {
  }

  ngOnInit(): void {
    if (this.nodeResolver.dataModel) {
      this.nodeData = this.nodeResolver.dataModel;
    }
    if (this.preference.dataModel) {
      this.preferenceData = this.preference.dataModel;
    }
    if (this.nodeData.user_privacy_policy_text && this.preferenceData.accepted_privacy_policy === "1970-01-01T00:00:00Z") {
      this.utilsService.acceptPrivacyPolicyDialog().subscribe();
    }
  }
}
