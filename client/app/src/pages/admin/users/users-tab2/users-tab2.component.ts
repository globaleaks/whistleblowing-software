import {Component, OnInit} from "@angular/core";
import {nodeResolverModel} from "@app/models/resolvers/node-resolver-model";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-users-tab2",
  templateUrl: "./users-tab2.component.html"
})
export class UsersTab2Component implements OnInit {
  nodeData: nodeResolverModel;

  constructor(private nodeResolver: NodeResolver, private utilsService: UtilsService) {
  }

  ngOnInit(): void {
    if (this.nodeResolver.dataModel) {
      this.nodeData = this.nodeResolver.dataModel;
    }
  }

  updateNode() {
    this.utilsService.update(this.nodeData).subscribe(_ => {
      this.utilsService.reloadComponent();
    });
  }
}