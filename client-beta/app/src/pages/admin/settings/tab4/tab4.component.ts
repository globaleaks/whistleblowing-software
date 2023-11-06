import {Component, Input} from "@angular/core";
import {NgForm} from "@angular/forms";
import {LanguageUtils} from "@app/pages/admin/settings/helper-methods/language-utils";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-tab4",
  templateUrl: "./tab4.component.html"
})
export class Tab4Component {
  @Input() contentForm: NgForm;

  vars: any = {};
  custom_texts: any = {};
  default_texts: any = {};
  custom_texts_selector: any[] = [];
  customTextsExist: boolean = false;
  languageUtils:LanguageUtils


  constructor(protected utilsService: UtilsService, protected nodeResolver: NodeResolver) {
  }

  ngOnInit(): void {
    this.initLanguages();
  }

  initLanguages(): void {
    this.languageUtils = new LanguageUtils(this.nodeResolver);
    this.languageUtils.updateLanguages();

    this.vars = {
      "language_to_customize": this.nodeResolver.dataModel.default_language
    };
    this.getl10n(this.vars.language_to_customize);
  }


  getl10n(lang: any): void {
    if (!lang) {
      return;
    }
    this.utilsService.AdminL10NResource(lang).subscribe(res => {
      this.custom_texts = res;
      this.customTextsExist = Object.keys(this.custom_texts).length > 0;
    });

    this.customTextsKeys();
    this.utilsService.DefaultL10NResource(lang).subscribe(default_texts => {
      const list = [];
      for (const key in default_texts) {
        if (Object.prototype.hasOwnProperty.call(default_texts, key)) {
          let value = default_texts[key];
          if (value.length > 150) {
            value = value.slice(0, 150) + "...";
          }
          list.push({"key": key, "value": value});
        }
      }
      this.default_texts = default_texts;
      this.custom_texts_selector = list.sort((a, b) => a.value.localeCompare(b.value));
    });
  }

  customTextsKeys(): { key: string }[] {
    return Object.keys(this.custom_texts).map(key => ({key}));
  }

  updateCustomText(data: any, lang: any) {
    this.utilsService.updateAdminL10NResource(data, lang).subscribe(_ => {
    });
  }

  deleteCustomText(dict: any, key: string): void {
    delete dict[key];
  }

}