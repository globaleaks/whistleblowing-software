import {Component} from "@angular/core";
import {QuestionnairesResolver} from "@app/shared/resolvers/questionnaires.resolver";
import {UtilsService} from "@app/shared/services/utils.service";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";

@Component({
  selector: "src-sites-tab2",
  templateUrl: "./sites-tab2.component.html"
})
export class SitesTab2Component {

  constructor(protected nodeResolver: NodeResolver, protected utilsService: UtilsService, public questionnairesResolver: QuestionnairesResolver) {
    console.log(nodeResolver.dataModel)
  }
}