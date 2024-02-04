import {Component} from "@angular/core";
import {PreferenceTab1Component} from "@app/shared/partials/preference-tabs/preference-tab1/preference-tab1.component";
import {PreferenceTab2Component} from "@app/shared/partials/preference-tabs/preference-tab2/preference-tab2.component";

@Component({
  selector: "src-preferences",
  templateUrl: "./preferences.component.html"
})
export class PreferencesComponent {
  activeTab: string = "tab1";

  tabs = [
    {
      id: "tab1",
      title: "Preferences",
      component: PreferenceTab1Component
    },
    {
      id: "tab2",
      title: "Password",
      component: PreferenceTab2Component
    }
  ];
}