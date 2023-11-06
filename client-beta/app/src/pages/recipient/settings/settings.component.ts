import {AfterViewInit, ChangeDetectorRef, Component, TemplateRef, ViewChild} from "@angular/core";
import {Router} from "@angular/router";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";

@Component({
  selector: "src-settings",
  templateUrl: "./settings.component.html"
})
export class SettingsComponent implements AfterViewInit {
  @ViewChild("tab1") tab1!: TemplateRef<any>;
  tabs: any[];
  nodeData: any;
  active: string;

  constructor(private cdr: ChangeDetectorRef, private preferenceResolver: PreferenceResolver, private router: Router) {
    if(!this.preferenceResolver.dataModel.can_edit_general_settings){
      this.router.navigate(['recipient/home']);
    }
  }

  ngAfterViewInit(): void {
    this.active = "Settings";

    this.tabs = [
      {
        title: "Settings",
        component: this.tab1
      },
    ];
    this.cdr.detectChanges();
  }
}

