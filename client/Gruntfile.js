/* eslint no-console: 0 */

module.exports = function(grunt) {
  var fs = require("fs"),
    path = require("path"),
    superagent = require("superagent"),
    gettextParser = require("gettext-parser"),
    Gettext = require("node-gettext");

  var fileToDataURI = function(filepath) {
    try {
      var mimeMap = {
        "css": "text/css",
        "ico": "image/x-icon",
        "js": "application/javascript",
        "png": "image/png",
        "woff": "application/woff"
      };

      var ext = filepath.split(".").pop();
      var mimetype = (ext in mimeMap) ? mimeMap[ext] : "application/octet-stream";

      return "data:" + mimetype + ";charset=utf-8;base64," + new Buffer(fs.readFileSync(filepath)).toString("base64");
    } catch (e) {
      return filepath;
    }
  };

  grunt.initConfig({
    eslint: {
      options: {
        configFile: "../.eslintrc.json"
      },
      src: [
        "Gruntfile.js",
        "app/js/**/*.js",
        "!app/lib/js/*.js",
        "!app/lib/js/locale/*.js",
        "tests/*.js"
      ]
    },

    clean: {
      all: ["build", "tmp"]
    },

    copy: {
      sources: {
        files: [
          { dest: "app/lib/css/", cwd: ".", src: ["node_modules/angular/angular-csp.css"], expand: true, flatten: true },
          { dest: "app/lib/css/", cwd: ".", src: ["node_modules/ui-bootstrap4/dist/ui-bootstrap-csp.css"], expand: true, flatten: true },
          { dest: "app/lib/css/", cwd: ".", src: ["node_modules/bootstrap/dist/css/bootstrap.css"], expand: true, flatten: true },
          { dest: "app/lib/css/", cwd: ".", src: ["node_modules/@fortawesome/fontawesome-free/css/fontawesome.css"], expand: true, flatten: true },
          { dest: "app/lib/css/", cwd: ".", src: ["node_modules/@fortawesome/fontawesome-free/css/regular.css"], expand: true, flatten: true },
          { dest: "app/lib/css/", cwd: ".", src: ["node_modules/@fortawesome/fontawesome-free/css/solid.css"], expand: true, flatten: true },
          { dest: "app/lib/css/", cwd: ".", src: ["node_modules/ui-select/dist/select.css"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/fast-sha256/sha256.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/@flowjs/flow.js/dist/flow.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/@flowjs/ng-flow/dist/ng-flow.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/angular/angular.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/angular-aria/angular-aria.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/angular-dynamic-locale/dist/tmhDynamicLocale.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/angular-file-saver/dist/angular-file-saver.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/angular-filter/dist/angular-filter.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/angular-qrcode/angular-qrcode.js"], expand: true, flatten: true},
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/angular-resource/angular-resource.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/angular-route/angular-route.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/angular-sanitize/angular-sanitize.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/angular-translate/dist/angular-translate.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/angular-translate-loader-static-files/angular-translate-loader-static-files.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/file-saver/FileSaver.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/ng-csv/build/ng-csv.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/ng-showdown/dist/ng-showdown.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/qrcode-generator/qrcode.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/showdown/dist/showdown.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/stacktrace-js/dist/stacktrace.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/ui-bootstrap4/dist/ui-bootstrap-tpls.js"], expand: true, flatten: true },
          { dest: "app/lib/js/", cwd: ".", src: ["node_modules/ui-select/dist/select.js"], expand: true, flatten: true },
          { dest: "app/lib/js/locale", cwd: ".", src: ["node_modules/angular-i18n/angular-locale*"], expand: true, flatten: true },
          { dest: "app/lib/webfonts", cwd: ".", src: ["node_modules/fontsource-metropolis/files/*"], expand: true, flatten: true },
          { dest: "app/lib/webfonts", cwd: ".", src: ["node_modules/@fortawesome/fontawesome-free/webfonts/*"], expand: true, flatten: true }
        ]
      },
      build: {
        files: [{ dest: "tmp/", cwd: "app/", src: ["**"], expand: true }]
      },
      package: {
        files: [
          {
            dest: "build/",
            cwd: "./tmp/",
            src: [
              "index.html",
              "license.txt",
              "css/styles.css",
              "js/scripts.js",
              "data/**",
              "lib/js/locale/**"
            ],
            expand: true,
            flatten: false
          }
        ]
      },
      coverage: {
        files: [{
          dest: "build/",
          cwd: "app/",
          src: [
            "**",
            "!js/**/*.js", // Don't copy scripts that will be instrumented,
            "lib/js/*.js", // and copy scripts that should not be instrumented.
            "lib/js/locale/*.js"
          ],
          expand: true
        }]
      }
    },

    useminPrepare: {
      html: [
        "tmp/index.html"
      ],
      options: {
        staging: "tmp",
        dest: "tmp",
        flow: {
          steps: {
            js: ["concat"],
            css: ["concat"]
          },
          post: {}
        }
      }
    },

    usemin: {
      html: [
        "tmp/index.html"
      ],
      options: {
        dirs: ["tmp"]
      }
    },

    // Put all angular.js templates into a single file
    ngtemplates:  {
      GL: {
        cwd: "app",
        options: {
          base: "app/",
          quotes: "single"
        },
        src: ["views/**/*.html"],
        dest: "tmp/js/templates.js"
      }
    },

    "string-replace": {
      pass1: {
        files: {
          "tmp/css/styles.css": "tmp/css/styles.css"
        },
        options: {
          replacements: [
            {
              pattern: "src: url('../lib/webfonts/metropolis-all-400-normal.woff') format('woff');",
              replacement: function () {
                return "src:url('" + fileToDataURI("tmp/lib/webfonts/metropolis-all-400-normal.woff") + "') format('woff');";
              }
            },
            {
              pattern: "src: url('../lib/webfonts/metropolis-all-700-normal.woff') format('woff');",
              replacement: function () {
                return "src:url('" + fileToDataURI("tmp/lib/webfonts/metropolis-all-700-normal.woff") + "') format('woff');";
              }
            },
            {
              pattern: "src: url(\"../webfonts/fa-regular-400.eot\");",
              replacement: ""
            },
            {
              pattern: "src: url(\"../webfonts/fa-regular-400.eot?#iefix\") format(\"embedded-opentype\"), url(\"../webfonts/fa-regular-400.woff2\") format(\"woff2\"), url(\"../webfonts/fa-regular-400.woff\") format(\"woff\"), url(\"../webfonts/fa-regular-400.ttf\") format(\"truetype\"), url(\"../webfonts/fa-regular-400.svg#fontawesome\") format(\"svg\"); }",
              replacement: function () {
                return "src:url('" + fileToDataURI("tmp/lib/webfonts/fa-regular-400.woff") + "') format('woff'); }";
              }
            },
            {
              pattern: "src: url(\"../webfonts/fa-solid-900.eot\");",
              replacement: ""
            },
            {
              pattern: "src: url(\"../webfonts/fa-solid-900.eot?#iefix\") format(\"embedded-opentype\"), url(\"../webfonts/fa-solid-900.woff2\") format(\"woff2\"), url(\"../webfonts/fa-solid-900.woff\") format(\"woff\"), url(\"../webfonts/fa-solid-900.ttf\") format(\"truetype\"), url(\"../webfonts/fa-solid-900.svg#fontawesome\") format(\"svg\"); }",
              replacement: function () {
                return "src:url('" + fileToDataURI("tmp/lib/webfonts/fa-solid-900.woff") + "') format('woff'); }";
              }
            },
            {
              pattern: /(0056b3|17a2b8|28a745|34ce57)/ig,
              replacement: function () {
                return "377abc";
              }
            },
            {
              pattern: /007bff/ig,
              replacement: function () {
                return "2066a2";
              }
            },
            {
              pattern: /40,167,69/ig,
              replacement: function () {
                return "56,119,188";
              }
            },
            {
              pattern: /0069d9/ig,
              replacement: function () {
                return "5797d5";
              }
            },
            {
              pattern: /005cbf/ig,
              replacement: function () {
                return "79B0e6";
              }
            },
            {
              pattern: /0062cc/ig,
              replacement: function () {
                return "9fc9f1";
              }
            },
            {
              pattern: /6c757d/ig,
              replacement: function () {
                return "58606e";
              }
            },
            {
              pattern: /5a6268/ig,
              replacement: function () {
                return "707a8a";
              }
            },
            {
              pattern: /4e555b/ig,
              replacement: function () {
                return "8e99aB";
              }
            },
            {
              pattern: /(545b62)/ig,
              replacement: function () {
                return "afbacc";
              }
            },
            {
              pattern: /(28a745|20c997)/ig,
              replacement: function () {
                return "2a854e";
              }
            },
            {
              pattern: /218838/ig,
              replacement: function () {
                return "3ba164";
              }
            },
            {
              pattern: /1e7e34/ig,
              replacement: function () {
                return "57c282";
              }
            },
            {
              pattern: /1c7430/ig,
              replacement: function () {
                return "7ddba3";
              }
            },
            {
              pattern: /ffc107/ig,
              replacement: function () {
                return "Fed644";
              }
            },
            {
              pattern: /e0a800/ig,
              replacement: function () {
                return "Faebb6";
              }
            },
            {
              pattern: /d39e00/ig,
              replacement: function () {
                return "faf2d4";
              }
            },
            {
              pattern: /c69500/ig,
              replacement: function () {
                return "faf8f0";
              }
            },
            {
              pattern: /dc3545/ig,
              replacement: function () {
                return "de1b1b";
              }
            },
            {
              pattern: /c82333/ig,
              replacement: function () {
                return "f55353";
              }
            },
            {
              pattern: /b21f2d/ig,
              replacement: function () {
                return "fa8e8e";
              }
            },
            {
              pattern: /bd2130/ig,
              replacement: function () {
                return "fab6b6";
              }
            },
            {
              pattern: /(e9ecef|f8f9fa)/ig,
              replacement: function () {
                return "f5f7fa";
              }
            },
            {
              pattern: /(212529|343a40)/ig,
              replacement: function () {
                return "1d1f24";
              }
            },
            {
              pattern: /(#CED4DA|#DEE2E6|rgba\(0,0,0,.125\))/ig,
              replacement: function () {
                return "#c8d1e0";
              }
            },
            {
              pattern: /fff3cd/ig,
              replacement: function () {
                return "fffcF1";
              }
            },
            {
              pattern: /(b8daff|d6d8db|c3e6cb|f5c6cb|ffeeba)/ig,
              replacement: function () {
                return "c8d1e0";
              }
            },
            {
              pattern: /155724|#383d41|721c24|856404/ig,
              replacement: function () {
                return "1d1f24";
              }
            },
            {
              pattern: /(rgba\(0,0,0,\.03\)|rgba\(0,0,0,\.05\))/ig,
              replacement: function () {
                return "#f5f7fa";
              }
            }
          ]
        }
      },
      pass2: {
        files: {
          "tmp/js/scripts.js": "tmp/js/scripts.js"
        },
        options: {
          replacements: [
            {
              pattern: "style=\"outline: 0;\"",
              replacement: "ng-style=\"{\\'outline\\': \\'0\\'}\""
            },
            {
              pattern: "style=\"margin-right: 10px\"",
              replacement: "ng-style=\"{\\'margin-right\\': \\'10px\\'}\""
            },
            {
              pattern: "style=\"width: 34px;\"",
              replacement: "ng-style=\"{\\'width\\': \\'34px\\'}\""
            }
          ]
        }
      },
      pass3: {
        files: {
          "tmp/index.html": "tmp/index.html"
        },
        options: {
          replacements: [
            {
              pattern: "<link rel=\"stylesheet\" href=\"css/styles.css\">",
              replacement: ""
            },
            {
              pattern: "<script src=\"js/scripts.js\"></script>",
              replacement: function() {
                return fs.readFileSync("tmp/loader.html");
              }
            }
          ]
        }
      }
    },

    confirm: {
      "pushTranslationsSource": {
        options: {
          // Static text.
          question: "WARNING:\n"+
                    "this task may cause translations loss and should be executed only on master branch.\n\n" +
                    "Are you sure you want to proceed (Y/N)?",
          input: "_key:y"
        }
      }
    },

    postcss: {
      options: {
        processors: [
          require("postcss-rtl")()
        ]
      },
      dist: {
        src: "tmp/lib/css/*.css"
      }
    },

    cssmin: {
      options: {
        sourceMap: true
      },
      minify: {
        files: {
          "build/css/styles.min.css": ["build/css/styles.css"]
        }
      }
    },

    stylelint: {
      options: {
        configFile: '.stylelintrc',
        formatter: 'string',
        ignoreDisables: false,
        failOnError: true,
        outputFile: '',
        reportNeedlessDisables: false,
        fix: false,
        syntax: ''
      },
      all: ["app/css/**/*.css"]
    },

    terser: {
      options: {
        sourceMap: true
      },
      minify: {
        files: {
          "build/js/scripts.min.js": ["build/js/scripts.js"]
        }
      }
    }
  });

  grunt.loadNpmTasks("grunt-angular-templates");
  grunt.loadNpmTasks("grunt-confirm");
  grunt.loadNpmTasks("grunt-contrib-clean");
  grunt.loadNpmTasks("grunt-contrib-concat");
  grunt.loadNpmTasks("grunt-contrib-copy");
  grunt.loadNpmTasks("grunt-contrib-cssmin");
  grunt.loadNpmTasks("grunt-postcss");
  grunt.loadNpmTasks("grunt-stylelint");
  grunt.loadNpmTasks("grunt-string-replace");
  grunt.loadNpmTasks("grunt-terser");
  grunt.loadNpmTasks("grunt-usemin");
  grunt.loadNpmTasks("gruntify-eslint");

  var readNoTranslateStrings = function() {
    return JSON.parse(grunt.file.read("app/data_src/notranslate_strings.json"));
  };

  var notranslate_strings = readNoTranslateStrings();

  function str_escape (val) {
    if (typeof(val) !== "string") {
      return val;
    }

    return val.replace(/[\n]/g, "\\n").replace(/[\t]/g, "\\r");
  }

  function str_unescape (val) {
    if (typeof(val) !== "string") {
      return val;
    }

    return val.replace(/\\n/g, "\n").replace(/\\t/g, "\t");
  }

  function readTransifexrc(){
    var transifexrc = fs.realpathSync(process.env.HOME + "/.transifexrc"),
        usernameRegexp = /username = (.*)/,
        passwordRegexp = /password = (.*)/,
        login = {},
        content;

    content = grunt.file.read(transifexrc);
    login.username = usernameRegexp.exec(content)[1];
    login.password = passwordRegexp.exec(content)[1];
    return login;
  }

  var agent = superagent.agent(),
    baseurl = "https://www.transifex.com/api/2/project/globaleaks",
    sourceFile = "pot/en.po";

  function updateTxSource(cb){
    var url = baseurl + "/resource/master/content/",
      content = grunt.file.read(sourceFile),
      login = readTransifexrc();

    agent.put(url)
      .auth(login.username, login.password)
      .set("Content-Type", "application/json")
      .send({"content": content})
      .end(function(err, res){
        if (res) {
          if (res.ok) {
            cb();
          } else {
            console.log("Error: " + res.text);
          }
        } else {
          console.log("Error: failed to fetch resource " + url);
        }
      });
  }

  function listLanguages(cb){
    var url = baseurl + "/resource/master/?details",
      login = readTransifexrc();

    agent.get(url)
      .auth(login.username, login.password)
      .end(function(err, res){
        if (res) {
          if (res.ok) {
            var result = JSON.parse(res.text);
            cb(result);
          } else {
            console.log("Error: " + res.text);
          }
        } else {
          console.log("Error: failed to fetch resource");
        }
      });
  }

  function fetchTxTranslationsForLanguage(langCode, cb) {
    var resourceUrl = baseurl + "/resource/master/",
      login = readTransifexrc();

    var url = resourceUrl + "stats/" + langCode + "/";

    agent.get(url)
      .auth(login.username, login.password)
      .end(function(err, res){
        if (res) {
          if (res.ok) {
            var content = JSON.parse(res.text);

            // Add the new translations for languages translated above 50%
            if (content.translated_entities > content.untranslated_entities) {
              var url = resourceUrl + "translation/" + langCode + "/";
              agent.get(url)
                .auth(login.username, login.password)
                .end(function(err, res){
                  if (res) {
                    if (res.ok) {
                      cb(JSON.parse(res.text)["content"]);
                    } else {
                      console.log("Error: " + res.text);
                    }
                  } else {
                    console.log("Error: failed to fetch resource");
                  }
                });
            } else {
              cb();
            }
          } else {
            console.log("Error: " + res.text);
          }
        } else {
          console.log("Error: failed to fetch resource");
        }
      });
  }

  function fetchTxTranslations(cb){
    var fetched_languages = 0,
      total_languages,
      supported_languages = {};

    listLanguages(function(result) {
      result.available_languages = result.available_languages.sort(function(a, b) {
        if (a.code > b.code) {
          return 1;
        }

        if (a.code < b.code) {
          return -1;
        }

        return 0;
      });

      total_languages = result.available_languages.length;

      var fetchLanguage = function(language) {
        fetchTxTranslationsForLanguage(language.code, function(content){
          if (content) {
            var potFile = "pot/" + language.code + ".po";

            fs.writeFileSync(potFile, content);
            console.log("Fetched " + language.code);
            supported_languages[language.code] = language.name;
          }

          fetched_languages += 1;

          if (total_languages === fetched_languages) {
            var sorted_keys = Object.keys(supported_languages).sort();

            console.log("List of available translations:");

            for (var i in sorted_keys) {
              console.log(" { \"code\": \"" + sorted_keys[i] +
                          "\", \"name\": \"" + supported_languages[sorted_keys[i]] +"\" },");
            }

            cb(supported_languages);
          } else {
            fetchLanguage(result.available_languages[fetched_languages]);
          }
        });
      };

      fetchLanguage(result.available_languages[0]);
    });
  }

  grunt.registerTask("makeTranslationsSource", function() {
    var data = {
      "charset": "UTF-8",
      "headers": {
        "project-id-version": "GlobaLeaks",
        "language-team": "English (http://www.transifex.com/otf/globaleaks/language/en/)",
        "mime-version": "1.0",
        "content-type": "text/plain; charset=UTF-8",
        "content-transfer-encoding": "8bit",
        "language": "en",
        "plural-forms": "nplurals=2; plural=(n != 1);"
      },
      "translations": {
        "": {
        }
      }
    };

    var gt = new Gettext(),
      translationStringRegexpHTML1 = /"(.+?)"\s+\|\s+translate/gi,
      translationStringRegexpHTML2 = /translate>(.+?)</gi,
      translationStringRegexpJSON = /"en":\s?"(.+)"/gi;

    gt.setTextDomain("main");

    function addString(str) {
      if (notranslate_strings.indexOf(str) !== -1) {
        return;
      }

      data["translations"][""][str] = {
        "msgid": str,
        "msgstr": str
      };
    }

    function extractStringsFromHTMLFile(filepath) {
      var filecontent = grunt.file.read(filepath),
        result;

      result = translationStringRegexpHTML1.exec(filecontent);
      while (result) {
        addString(result[1]);
        result = translationStringRegexpHTML1.exec(filecontent);
      }

      result = translationStringRegexpHTML2.exec(filecontent);
      while (result) {
        addString(result[1]);
        result = translationStringRegexpHTML2.exec(filecontent);
      }

    }

    function extractStringsFromJSONFile(filepath) {
      var filecontent = grunt.file.read(filepath),
        result;

      result = translationStringRegexpJSON.exec(filecontent);
      while (result) {
        addString(result[1]);
        result = translationStringRegexpJSON.exec(filecontent);
      }
    }

    function extractStringsFromTXTFile(filepath) {
      var filecontent = grunt.file.read(filepath),
        lines = filecontent.split("\n");

      for (var i=0; i<lines.length; i++){
        // we skip adding empty strings and variable only strings
        if (lines[i] !== "" && !lines[i].match(/^{[a-zA-Z0-9]+}/g)) {
          addString(lines[i]);
        }
      }
    }

    function extractStringsFromFile(filepath) {
      var ext = filepath.split(".").pop();

      if (ext === "html") {
        extractStringsFromHTMLFile(filepath);
      } else if (ext === "json") {
        extractStringsFromJSONFile(filepath);
      } else if (ext === "txt") {
        extractStringsFromTXTFile(filepath);
      }
    }

    function extractStringsFromDir(dir) {
      grunt.file.recurse(dir, function(absdir, rootdir, subdir, filename) {
        var filepath = path.join(dir, subdir || "", filename || "");
        extractStringsFromFile(filepath);
      });
    }

    ["app/translations.html",
      "app/data_src/appdata.json",
      "app/data/field_attrs.json"].forEach(function(file) {
      extractStringsFromFile(file);
    });

    ["app/views",
      "app/data_src/questionnaires",
      "app/data_src/questions",
      "app/data_src/txt"].forEach(function(dir) {
      extractStringsFromDir(dir);
    });

    grunt.file.mkdir("pot");

    fs.writeFileSync("pot/en.po", gettextParser.po.compile(data), "utf8");

    console.log("Written " + Object.keys(data["translations"][""]).length + " string to pot/en.po.");
  });

  grunt.registerTask("☠☠☠pushTranslationsSource☠☠☠", function() {
    updateTxSource(this.async());
  });

  grunt.registerTask("fetchTranslations", function() {
    var done = this.async(),
      gt = new Gettext(),
      lang_code;

    gt.setTextDomain("main");

    fetchTxTranslations(function(supported_languages) {
      gt.addTranslations("en", "main", gettextParser.po.parse(fs.readFileSync("pot/en.po")));
      var strings = Object.keys(gettextParser.po.parse(fs.readFileSync("pot/en.po"))["translations"][""]);

      for (lang_code in supported_languages) {
        var translations = {}, output;

        gt.addTranslations(lang_code, "main", gettextParser.po.parse(fs.readFileSync("pot/" + lang_code + ".po")));

        gt.setLocale(lang_code);

        for (var i = 0; i < strings.length; i++) {
          if (strings[i] === "") {
            continue;
          }

          translations[strings[i]] = str_unescape(gt.gettext(str_escape(strings[i])));
        }

        output = JSON.stringify(translations, null, 2);

        fs.writeFileSync("app/data/l10n/" + lang_code + ".json", output);
      }

      done();
    });
  });

  grunt.registerTask("makeAppData", function() {
    var done = this.async(),
      gt = new Gettext(),
      supported_languages = [];

    gt.setTextDomain("main");

    grunt.file.recurse("pot/", function(absdir, rootdir, subdir, filename) {
      supported_languages.push(filename.replace(/.po$/, ""));
    });

    var appdata = JSON.parse(fs.readFileSync("app/data_src/appdata.json")),
      output = {},
      version = appdata["version"],
      templates = appdata["templates"],
      templates_sources = {};

    var translate_object = function(object, keys) {
      for (var k in keys) {
        if (object[keys[k]]["en"] === "")
          continue;

        supported_languages.forEach(function(lang_code) {
          gt.setLocale(lang_code);
          var translation = gt.gettext(str_escape(object[keys[k]]["en"]));
          if (translation !== undefined) {
            object[keys[k]][lang_code] = str_unescape(translation).trim();
          }
        });
      }
    };

    var translate_field = function(field) {
      var i;
      translate_object(field, ["label", "description", "hint"]);

      for (i in field["attrs"]) {
        translate_object(field["attrs"][i], ["value"]);
      }

      for (i in field["options"]) {
        translate_object(field["options"][i], ["label"]);
      }

      for (i in field["children"]) {
        translate_field(field["children"][i]);
      }
    };

    var translate_step = function(step) {
      translate_object(step, ["label", "description"]);

      for (var c in step["children"]) {
        translate_field(step["children"][c]);
      }
    };

    var translate_questionnaire = function(questionnaire) {
      questionnaire["steps"].forEach(function(step) {
        translate_step(step);
      });
    };

    gt.addTranslations("en", "main", gettextParser.po.parse(fs.readFileSync("pot/en.po")));

    grunt.file.recurse("app/data_src/txt", function(absdir, rootdir, subdir, filename) {
      var template_name = filename.split(".txt")[0],
        filepath = path.join("app/data_src/txt", subdir || "", filename || "");

      templates_sources[template_name] = grunt.file.read(filepath);
    });

    supported_languages.forEach(function(lang_code) {
      gt.setLocale(lang_code);
      gt.addTranslations(lang_code, "main", gettextParser.po.parse(fs.readFileSync("pot/" + lang_code + ".po")));

      for (var template_name in templates_sources) {
        if (!(template_name in templates)) {
          templates[template_name] = {};
        }

        var tmp = templates_sources[template_name];

        var lines = templates_sources[template_name].split("\n");

        for (var i=0; i<lines.length; i++) {
          var translation = gt.gettext(str_escape(lines[i]));
          if (translation === undefined) {
            continue;
          }

          // we skip adding empty strings and variable only strings
          if (lines[i] !== "" && !lines[i].match(/^{[a-zA-Z0-9]+}/g)) {
            tmp = tmp.replace(lines[i], str_unescape(translation));
          }
        }

        templates[template_name][lang_code] = tmp.trim();
      }
    });

    output["version"] = version;
    output["templates"] = templates;
    output["node"] = {};

    for (var k in appdata["node"]) {
      output["node"][k] = {};
      supported_languages.forEach(function(lang_code) {
        gt.setLocale(lang_code);
        output["node"][k][lang_code] = str_unescape(gt.gettext(str_escape(appdata["node"][k]["en"])));
      });
    }

    output = JSON.stringify(output, null, 2);

    fs.writeFileSync("app/data/appdata.json", output);

    grunt.file.recurse("app/data_src/questionnaires", function(absdir, rootdir, subdir, filename) {
      var srcpath = path.join("app/data_src/questionnaires", subdir || "", filename || "");
      var dstpath = path.join("app/data/questionnaires", subdir || "", filename || "");
      var questionnaire = JSON.parse(fs.readFileSync(srcpath));
      translate_questionnaire(questionnaire);
      fs.writeFileSync(dstpath, JSON.stringify(questionnaire, null, 2));
    });

    grunt.file.recurse("app/data_src/questions", function(absdir, rootdir, subdir, filename) {
      var srcpath = path.join("app/data_src/questions", subdir || "", filename || "");
      var dstpath = path.join("app/data/questions", subdir || "", filename || "");
      var field = JSON.parse(fs.readFileSync(srcpath));
      translate_field(field);
      fs.writeFileSync(dstpath, JSON.stringify(field, null, 2));
    });

    done();
  });

  grunt.registerTask("verifyAppData", function() {
    var app_data = JSON.parse(fs.readFileSync("app/data/appdata.json"));
    var var_map = JSON.parse(fs.readFileSync("app/data/templates_descriptor.json"));

    var failures = [];

    function recordFailure(template_name, lang, text, msg) {
      var line = template_name + " : "+ lang + " : " + msg;
      failures.push(line);
    }

    function checkIfRightTagsUsed(variables, lang, text, template_name, expected_tags) {
      expected_tags.forEach(function(tag) {
        if (text.indexOf(tag) === -1) {
          recordFailure(template_name, lang, text, "missing expected tag: " + tag);
        }
      });
    }

    function checkForBrokenTags(variables, lang, text, template_name) {
      var open_b = (text.match(/{/g) || []).length;
      var close_b = (text.match(/{/g) || []).length;

      var tags = text.match(/{[A-Z][a-zA-Z]+}/g) || [];

      if (open_b !== close_b) {
        recordFailure(template_name, lang, text, "brackets misaligned");
      }
      if (open_b !== tags.length) {
        recordFailure(template_name, lang, text, "malformed tags");
      }

      // Check to see there are no other commonly used tags inside like: () [] %%, {{}}
      if (text.match(/\([A-Z][a-zA-Z]+\)/g) !== null ||
          text.match(/\[[A-Z][a-zA-Z]+\]/g) !== null ||
          text.match(/%[A-Z][a-zA-Z]+%/g) !== null ||
          text.match(/{{[A-Z][a-zA-Z]+}}/g) !== null) {
        recordFailure(template_name, lang, text, "mistaken variable tags");
      }

      tags.forEach(function(tag) {
        if (variables.indexOf(tag) < 0) {
          recordFailure(template_name, lang, text, "invalid tag " + tag);
        }
      });
    }

    // Check_for_missing_templates
    for (var template_name in var_map) {
      var lang_map = app_data["templates"][template_name];
      var variables = var_map[template_name];
      var expected_tags = (lang_map["en"].match(/{[A-Z][a-zA-Z]+}/g) || []);

      for (var lang in lang_map) {
        var text = lang_map[lang];
        checkIfRightTagsUsed(variables, lang, text, template_name, expected_tags);
        checkForBrokenTags(variables, lang, text, template_name);
        // TODO Search for ://
        // TODO Check for html elements and other evil strings
      }
    }

    if (failures.length !== 0) {
      failures.forEach(function(failure) {
        console.log(failure);
      });

      grunt.fail.warn("verifyAppData task failure");
    } else {
      console.log("Successfully verified");
    }
  });

  // Run this task to push translations on transifex
  grunt.registerTask("pushTranslationsSource", ["confirm", "☠☠☠pushTranslationsSource☠☠☠"]);

  // Run this task to fetch translations from transifex and create application files
  grunt.registerTask("updateTranslations", ["fetchTranslations", "makeAppData", "verifyAppData"]);

  // Run this to build your app. You should have run updateTranslations before you do so, if you have changed something in your translations.
  grunt.registerTask("build",
    ["clean", "copy:sources", "copy:build", "ngtemplates", "postcss", "useminPrepare", "concat", "usemin", "string-replace", "copy:package", "cssmin", "terser"]);

  grunt.registerTask("instrument-client", [
    "clean",
    "copy:sources",
    "copy:coverage",
    "instrument"
  ]);
};
