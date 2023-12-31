import {Component} from "@angular/core";
import {JobResolver} from "@app/shared/resolvers/job.resolver";
import {jobResolverModel} from "@app/models/resolvers/job-resolver-model";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-auditlog-tab4",
  templateUrl: "./audit-log-tab4.component.html"
})
export class AuditLogTab4Component {
  currentPage = 1;
  pageSize = 20;
  jobs: jobResolverModel[] = [];

  constructor(private utilsService: UtilsService, private jobResolver: JobResolver) {
  }

  ngOnInit() {
    this.loadAuditLogData();
  }

  loadAuditLogData() {
    if (Array.isArray(this.jobResolver.dataModel)) {
      this.jobs = this.jobResolver.dataModel;
    } else {
      this.jobs = [this.jobResolver.dataModel];
    }
  }

  getPaginatedData(): jobResolverModel[] {
    const startIndex = (this.currentPage - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    return this.jobs.slice(startIndex, endIndex);
  }

  exportAuditLog() {
    this.utilsService.generateCSV(JSON.stringify(this.jobs), 'jobs', []);
  }
}