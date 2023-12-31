import {AfterViewInit, ChangeDetectorRef, Component, TemplateRef, ViewChild} from "@angular/core";
import {Router} from "@angular/router";
import {Tab} from "@app/models/component-model/tab";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {Tab1Component} from "@app/pages/admin/settings/tab1/tab1.component";

@Component({
  selector: "src-recipient-settings",
  templateUrl: "./settings.component.html"
})
export class SettingsComponent implements AfterViewInit {
  @ViewChild("tab1") tab1!: TemplateRef<Tab1Component>;
  tabs: Tab[];
  active: string;

  constructor(private cdr: ChangeDetectorRef, private preferenceResolver: PreferenceResolver, private router: Router) {
    if (!this.preferenceResolver.dataModel.can_edit_general_settings) {
      this.router.navigate(['recipient/home']).then();
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

