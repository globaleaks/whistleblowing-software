import {Component, OnInit} from "@angular/core";
import {ActivatedRoute} from "@angular/router";
import {HttpService} from "@app/shared/services/http.service";

@Component({
  selector: "src-activation",
  templateUrl: "./activation.component.html"
})
export class ActivationComponent implements OnInit {

  constructor(private route: ActivatedRoute, private httpService: HttpService) {
  }

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      if ("token" in params) {
        const token = params["token"];
        this.httpService.requestSignupToken(token).subscribe();
      }
    });
  }
}
