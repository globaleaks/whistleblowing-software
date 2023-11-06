export class LanguageUtils {
  public languages_supported: any = {};
  public languagesEnabled: any = {};
  public languages_enabled_selector: any[] = [];

  constructor(private nodeResolver: any) {}

  updateLanguages() {
    this.languages_supported = {};
    this.languagesEnabled = {};
    this.languages_enabled_selector = [];

    this.nodeResolver.dataModel.languages_supported.forEach((lang: any) => {
      this.languages_supported[lang.code] = lang;

      if (this.nodeResolver.dataModel.languages_enabled.indexOf(lang.code) !== -1) {
        this.languagesEnabled[lang.code] = lang;
        this.languages_enabled_selector.push(lang);
      }
    });
  }
}