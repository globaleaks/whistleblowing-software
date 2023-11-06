import {Component, OnInit} from "@angular/core";
import {RedirectsResolver} from "@app/shared/resolvers/redirects.resolver";
import {HttpService} from "@app/shared/services/http.service";

@Component({
  selector: "src-url-redirects",
  templateUrl: "./url-redirects.component.html"
})
export class UrlRedirectsComponent implements OnInit {
  redirectData: any = [];
  new_redirect: any = {
    path1: null,
    path2: null
  };

  constructor(private redirects: RedirectsResolver, private httpService: HttpService) {
  }

  ngOnInit(): void {
    this.redirectData = this.redirects.dataModel;
  }

  addRedirect() {
    const arg = {
      path1: this.new_redirect.path1,
      path2: this.new_redirect.path2
    };
    this.httpService.requestPostRedirectsResource(arg).subscribe((res) => {
      this.redirectData.push(res);
      this.new_redirect.path1 = "";
      this.new_redirect.path2 = "";
      this.getResolver();
    });
  }

  getResolver() {
    return this.httpService.requestRedirectsResource().subscribe(response => {
      this.redirectData = response;
    });
  }

  deleteRedirect(redirect: any) {
    this.httpService.requestDeleteRedirectsResource(redirect.id).subscribe(() => {
      this.getResolver();
    });
  }
}