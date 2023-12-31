import {ChangeDetectorRef, Component, Input, OnInit, ViewChild} from "@angular/core";
import {WbtipService} from "@app/services/helper/wbtip.service";
import {AuthenticationService} from "@app/services/helper/authentication.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {ScrollToBottomDirective} from "@app/shared/directive/scroll-to-bottom.directive";
import {ReceiverTipService} from "@app/services/helper/receiver-tip.service";
import {Comment} from "@app/models/app/shared-public-model";

@Component({
  selector: "src-tip-comments",
  templateUrl: "./tip-comments.component.html"
})
export class TipCommentsComponent implements OnInit {
  @Input() tipService: ReceiverTipService | WbtipService;
  @Input() key: string;
  @ViewChild(ScrollToBottomDirective)
  scroll: ScrollToBottomDirective;

  collapsed = false;
  newCommentContent = "";
  currentCommentsPage: number = 1;
  itemsPerPage = 5;
  comments: Comment[] = [];
  newComments: Comment;

  constructor(private rTipService: ReceiverTipService, protected authenticationService: AuthenticationService, protected utilsService: UtilsService, private cdr: ChangeDetectorRef) {

  }

  ngOnInit() {
    this.comments = this.tipService.tip.comments;
  }

  public toggleCollapse() {
    this.collapsed = !this.collapsed;
  }

  newComment() {
    let response = this.tipService.newComment(this.newCommentContent, this.key);
    this.newCommentContent = "";

    response.subscribe(
      (data) => {
        this.comments = this.tipService.tip.comments;
        this.tipService.tip.comments.push(data);
        this.comments = [...this.comments, this.newComments];
        this.cdr.detectChanges();
      }
    );
  }

  getSortedComments(data: Comment[]): Comment[] {
    return data;
  }

  onEnableTwoWayCommentsChange() {
    this.rTipService.operation("api/recipient/rtips/" + this.tipService.tip.id, "set", {
      "key": "enable_two_way_comments",
      "value": this.tipService.tip.enable_two_way_comments
    });
  }
}
