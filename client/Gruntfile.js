/* eslint no-console: 0 */

module.exports = function(grunt) {
  var fs = require('fs'),
      path = require('path'),
      superagent = require('superagent'),
      gettextParser = require("gettext-parser"),
      Gettext = require('node-gettext');

  var fileToDataURI = function(filepath) {
    try {
      var mimeMap = {
        'css': 'text/css',
        'ico': 'image/x-icon',
        'js': 'application/javascript',
        'png': 'image/png',
        'woff': 'application/woff'
      }

      var ext = filepath.split('.').pop();
      var mimetype = (ext in mimeMap) ? mimeMap[ext] : 'application/octet-stream';

      fs.accessSync(filepath, fs.F_OK);
      var filecontent = fs.readFileSync(filepath);

      return 'data:' + mimetype + ';charset=utf-8;base64,' + new Buffer(filecontent).toString('base64');
    } catch (e) {
      return filepath;
    }
  };

  grunt.initConfig({
    eslint: {
      src: [
        'Gruntfile.js',
        'app/js/**/*.js',
        '!app/js/lib/*.js',
        '!app/js/locale/*.js',
        '!app/js/crypto/lib/*.js',
        'tests/end2end/*.js',
        'tests/api/*.js'
      ]
    },

    clean: {
      all: ['tmp', 'build']
    },

    copy: {
      sources: {
        files: [
          { dest: 'app/css', cwd: '.', src: ['node_modules/bootstrap-inline-rtl/dist/css/bootstrap.css'], expand: true, flatten: true },
          { dest: 'app/css', cwd: '.', src: ['node_modules/ui-select/dist/select.min.css'], expand: true, flatten: true },
          { dest: 'app/fonts', cwd: '.', src: ['node_modules/bootstrap-inline-rtl/fonts/*'], expand: true, flatten: true },
          { dest: 'app/js/locale', cwd: '.', src: ['node_modules/angular-i18n/angular-locale*'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/stacktrace-js/dist/stacktrace.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/scrypt-async/scrypt-async.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/openpgp/dist/openpgp.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular/angular.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-aria/angular-aria.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-filter/dist/angular-filter.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-resource/angular-resource.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-route/angular-route.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-sanitize/angular-sanitize.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-translate/dist/angular-translate.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-translate-loader-url/angular-translate-loader-url.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-translate-loader-static-files/angular-translate-loader-static-files.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-ui-bootstrap/dist/ui-bootstrap-tpls.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/d3/dist/d3.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/file-saver/FileSaver.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-file-saver/dist/angular-file-saver.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/@flowjs/flow.js/dist/flow.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/@flowjs/ng-flow/dist/ng-flow.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/zxcvbn/dist/zxcvbn.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-zxcvbn/dist/angular-zxcvbn.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/angular-dynamic-locale/tmhDynamicLocale.min.js'], expand: true, flatten: true },
          { dest: 'app/js/lib/', cwd: '.', src: ['node_modules/ui-select/dist/select.min.js'], expand: true, flatten: true },
          { dest: 'app/js/crypto/lib/', cwd: '.', src: ['node_modules/openpgp/dist/openpgp.min.js'], expand: true, flatten: true },
          { dest: 'app/js/crypto/lib/', cwd: '.', src: ['node_modules/openpgp/dist/openpgp.worker.min.js'], expand: true, flatten: true },
          { dest: 'app/js/crypto/lib/', cwd: '.', src: ['node_modules/scrypt-async/scrypt-async.min.js'], expand: true, flatten: true }
        ]
      },
      build: {
        files: [{ dest: 'tmp/', cwd: 'app/', src: ['**'], expand: true }]
      },
      end2end_coverage: {
          files: [{
            dest: 'build/',
            cwd: 'app/',
            src: [
              '**',
              '!js/**/*.js', // Don't copy scripts that will be instrumented,
              'js/lib/*.js', // and copy scripts that should not be instrumented.
              'js/locale/*.js',
              'js/crypto/lib/*.js'
            ],
            expand: true
          }]
      },
    },

    browserify: {
      unittest: {
        files: {
          'tests/unit/lib/unittest-bundle.js': 'tests/unit/unittest.js'
        },
      }
    },

    useminPrepare: {
      html: [
        'tmp/index.html'
      ],
      options: {
        staging: 'tmp',
        dest: 'tmp',
        flow: {
          steps: {
            js: ['concat'], // we avoid to minify intentionally! #1417 !
            css: ['concat']
          },
          post: {}
        }
      }
    },

    usemin: {
      html: [
        'tmp/index.html',
        'tmp/views/**/*.html'
      ],
      options: {
        dirs: ['tmp']
      }
    },

    html: {
      files: ['**/*.html']
    },

    // Put all angular.js templates into a single file
    ngtemplates:  {
      GLClient: {
        cwd: 'app',
        options: {
          base: 'app/',
          quotes: 'single'
        },
        src: ['views/**/*.html'],
        dest: 'tmp/js/templates.js'
      }
    },

    mochaTest: {
      test: {
        options: {
          timeout: 30000,
          reporter: 'list',
        },
        src: ['tests/api/test.js'],
      },
    },

    'string-replace': {
      pass1: {
        files: {
          'tmp/index.html': 'tmp/index.html',
          'tmp/css/styles.css': 'tmp/css/styles.css',
          'tmp/js/scripts.js': 'tmp/js/scripts.js'
        },
        options: {
          replacements: [
            {
              pattern: '<script src="js/scripts.js"></script>',
              replacement: ''
            },
            {
              pattern: '<!-- start_globaleaks(); -->',
              replacement: 'start_globaleaks();'
            },
            {
              pattern: "src: url('../fonts/glyphicons-halflings-regular.eot');",
              replacement: ''
            },
            {
              pattern: "src: url('../fonts/glyphicons-halflings-regular.eot?#iefix') format('embedded-opentype'), url('../fonts/glyphicons-halflings-regular.woff2') format('woff2'), url('../fonts/glyphicons-halflings-regular.woff') format('woff'), url('../fonts/glyphicons-halflings-regular.ttf') format('truetype'), url('../fonts/glyphicons-halflings-regular.svg#glyphicons_halflingsregular') format('svg');",
              replacement: function () {
                return "src: url('" + fileToDataURI('tmp/fonts/glyphicons-halflings-regular.woff') + "') format('woff');";
              }
            },
            {
              pattern: /js\/locale\/([^'")]+)*/g,
              replacement: function (match) {
                return fileToDataURI('tmp/' + match);
              }
            }
          ]
        }
      },
      pass2: {
        files: {
          'tmp/index.html': 'tmp/index.html'
        },
        options: {
          replacements: [
            {
              pattern: 'css/styles.css',
              replacement: function () {
                return fileToDataURI('tmp/css/styles.css');
              }
            }
          ]
        }
      },
      pass3: {
        files: {
          'tmp/js/crypto/scrypt-async.worker.js': 'tmp/js/crypto/scrypt-async.worker.js'
        },
        options: {
          replacements: [
            {
              pattern: 'scrypt-async.min.js',
              replacement: function () {
                return fileToDataURI('tmp/js/crypto/scrypt-async.min.js');
              }
            }
          ]
        }
      }
    },

    compress: {
      main: {
        options: {
          mode: 'gzip'
        },
        expand: true,
        cwd: 'build/',
        src: ['index.html', 'license.txt', 'js/*'],
        dest: 'build/',
        rename: function(dest, src) {
          return dest + '/' + src + '.gz';
        }
      }
    },

    confirm: {
      'pushTranslationsSource': {
        options: {
          // Static text.
          question: 'WARNING:\n'+
                    'this task may cause translations loss and should be executed only on master branch.\n\n' +
                    'Are you sure you want to proceed (Y/N)?',
          input: '_key:y'
        }
      }
    },

    instrument: {
      build: {
        files: 'js/**/*.js',
        options: {
          lazy: true,
          cwd: 'app/',
          basePath: 'build/'
        }
      }
    },

    protractor_coverage: {
      local: {
        options: {
          configFile: 'tests/end2end/protractor-coverage.config.js'
        }
      }
    },

    makeReport: {
      src: 'coverage/*.json',
      options: {
        type: 'lcov',
        dir: 'coverage',
        print: 'detail'
      }
    }
  });

  // Prefer explicit to loadNpmTasks to:
  //   require('matchdep').filterDev('grunt-*').forEach(grunt.loadNpmTasks);
  //
  // the reasons is during time strangely the automating loading was causing problems.
  grunt.loadNpmTasks('grunt-angular-templates');
  grunt.loadNpmTasks('grunt-confirm');
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-compress');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-connect');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-istanbul');
  grunt.loadNpmTasks('grunt-protractor-coverage');
  grunt.loadNpmTasks('grunt-string-replace');
  grunt.loadNpmTasks('grunt-usemin');
  grunt.loadNpmTasks('grunt-mocha-test');
  grunt.loadNpmTasks("gruntify-eslint");

  var readNoTranslateStrings = function() {
    return JSON.parse(grunt.file.read('app/data_src/notranslate_strings.json'));
  };

  var notranslate_strings = readNoTranslateStrings();

  grunt.registerTask('cleanupWorkingDirectory', function() {
    var x;
    var dirs;

    var rm_rf = function(dir) {
      var s = fs.statSync(dir);

      if (!s.isDirectory()) {return fs.unlinkSync(dir);}

      fs.readdirSync(dir).forEach(function(f) {
        rm_rf(path.join(dir || '', f || ''));
      });

      fs.rmdirSync(dir);
    };

    grunt.file.mkdir('build/');

    grunt.file.copy('tmp/index.html', 'build/index.html');
    grunt.file.copy('tmp/license.txt', 'build/license.txt');
    grunt.file.copy('tmp/js/scripts.js', 'build/js/scripts.js');
    grunt.file.copy('tmp/js/plugin.js', 'build/js/plugin.js');

    grunt.file.mkdir('build/js/crypto/');
    grunt.file.copy('tmp/js/crypto/scrypt-async.worker.js', 'build/js/crypto/scrypt-async.worker.js');

    var copy_fun = function(absdir, rootdir, subdir, filename) {
      grunt.file.copy(absdir, path.join('build/' + dirs[x], subdir || '', filename || ''));
    };

    dirs = ['js/crypto/lib', 'l10n', 'data'];
    for (x in dirs) {
      grunt.file.recurse('tmp/' + dirs[x], copy_fun);
    }

    rm_rf('tmp');
  });

  function str_escape (val) {
      if (typeof(val) !== "string") {
        return val;
      }

      return val.replace(/[\n]/g, '\\n').replace(/[\t]/g, '\\r');
  }

  function str_unescape (val) {
      if (typeof(val) !== "string") {
        return val;
      }

      return val.replace(/\\n/g, '\n').replace(/\\t/g, '\t');
  }

  function readTransifexrc(){
    var transifexrc = fs.realpathSync(process.env.HOME + '/.transifexrc'),
      err = fs.stat(transifexrc),
      usernameRegexp = /username = (.*)/,
      passwordRegexp = /password = (.*)/,
      content, login = {};

    if (err) {
      console.log(transifexrc + " does not exist");
      console.log("It should contain");
      console.log("username = <your username>");
      console.log("password = <your password>");
      throw 'No transifexrc file';
    }

    content = grunt.file.read(transifexrc);
    login.username = usernameRegexp.exec(content)[1];
    login.password = passwordRegexp.exec(content)[1];
    return login;
  }

  var agent = superagent.agent(),
    baseurl = 'https://www.transifex.com/api/2/project/globaleaks',
    sourceFile = 'pot/en.po';

  function updateTxSource(cb){
    var url = baseurl + '/resource/master/content/',
      content = grunt.file.read(sourceFile),
      login = readTransifexrc();

    agent.put(url)
      .auth(login.username, login.password)
      .set('Content-Type', 'application/json')
      .send({'content': content})
      .end(function(err, res){
        if (res) {
          if (res.ok) {
            cb();
          } else {
           console.log('Error: ' + res.text);
          }
        } else {
          console.log('Error: failed to fetch resource ' + url);
        }
    });
  }

  function listLanguages(cb){
    var url = baseurl + '/resource/master/?details',
      login = readTransifexrc();

    agent.get(url)
      .auth(login.username, login.password)
      .end(function(err, res){
        if (res) {
          if (res.ok) {
            var result = JSON.parse(res.text);
            cb(result);
          } else {
            console.log('Error: ' + res.text);
          }
        } else {
          console.log('Error: failed to fetch resource');
        }
    });
  }

  function fetchTxTranslationsForLanguage(langCode, cb) {
    var resourceUrl = baseurl + '/resource/master/',
      login = readTransifexrc();

    var url = resourceUrl + 'stats/' + langCode + '/';

    agent.get(url)
      .auth(login.username, login.password)
      .end(function(err, res){
        if (res) {
          if (res.ok) {
            var content = JSON.parse(res.text);

            if (content.translated_entities > content.untranslated_entities) {
              var url = resourceUrl + 'translation/' + langCode + '/';
              agent.get(url)
                .auth(login.username, login.password)
                .end(function(err, res){
                  if (res) {
                    if (res.ok) {
                      cb(JSON.parse(res.text)['content']);
                    } else {
                      console.log('Error: ' + res.text);
                    }
                  } else {
                    console.log('Error: failed to fetch resource');
                  }
              });
            } else {
              cb();
            }
          } else {
            console.log('Error: ' + res.text);
          }
        } else {
          console.log('Error: failed to fetch resource');
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

  grunt.registerTask('makeTranslationsSource', function() {
    var data = {
      "charset": "UTF-8",
      "headers": {
        "Project-Id-Version": "GlobaLeaks\n",
        "Language-Team": "English (http://www.transifex.com/otf/globaleaks/language/en/)\n",
        "MIME-Version": "1.0\n",
        "Content-Type": "text/plain; charset=UTF-8\n",
        "Content-Transfer-Encoding": "8bit\n",
        "Language": "en\n",
        "Plural-Forms": "nplurals=2; plural=(n != 1);\n"
      },
      "translations": {
        "": {
        }
      }
    }

    var gt = new Gettext(),
      translationStringRegexpHTML1 = /"(.+?)"\s+\|\s+translate/gi,
      translationStringRegexpHTML2 = /translate>(.+?)</gi,
      translationStringRegexpJSON = /"en":\s?"(.+)"/gi;

    gt.setTextDomain('main');

    function addString(str) {
      if (notranslate_strings.indexOf(str) !== -1) {
        return;
      }

      data['translations'][''][str] = {
        "msgid": str,
        "msgstr": str
      }
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
        if (lines[i] !== '' && !lines[i].match(/^{[a-zA-Z0-9]+}/g)) {
          addString(lines[i]);
        }
      }
    }

    function extractStringsFromFile(filepath) {
      var ext = filepath.split('.').pop();

      if (ext === 'html') {
        extractStringsFromHTMLFile(filepath);
      } else if (ext === 'json') {
        extractStringsFromJSONFile(filepath);
      } else if (ext === 'txt') {
        extractStringsFromTXTFile(filepath);
      }
    }

    function extractStringsFromDir(dir) {
      grunt.file.recurse(dir, function(absdir, rootdir, subdir, filename) {
        var filepath = path.join(dir, subdir || '', filename || '');
        extractStringsFromFile(filepath);
      });
    }

    ['app/translations.html',
     'app/data_src/appdata.json',
     'app/data_src/field_attrs.json'].forEach(function(file) {
      extractStringsFromFile(file);
    });

    ['app/views',
     'app/data_src/questionnaires',
     'app/data_src/questions',
     'app/data_src/txt'].forEach(function(dir) {
      extractStringsFromDir(dir);
    });

    grunt.file.mkdir("pot");

    fs.writeFileSync("pot/en.po", gettextParser.po.compile(data), 'utf8');

    console.log("Written " + data['translations'][''].length + " string to pot/en.po.");
  });

  grunt.registerTask('☠☠☠pushTranslationsSource☠☠☠', function() {
    updateTxSource(this.async());
  });

  grunt.registerTask('fetchTranslations', function() {
    var done = this.async(),
      gt = new Gettext(),
      lang_code;

    gt.setTextDomain('main');

    fetchTxTranslations(function(supported_languages) {
      gt.addTranslations("en", 'main', gettextParser.po.parse(fs.readFileSync("pot/en.po")));
      var strings = Object.keys(gettextParser.po.parse(fs.readFileSync("pot/en.po"))['translations']['']);

      for (lang_code in supported_languages) {
        var translations = {}, output;

        gt.addTranslations(lang_code, 'main', gettextParser.po.parse(fs.readFileSync("pot/" + lang_code + ".po")));

        gt.setLocale(lang_code);

        for (var i = 0; i < strings.length; i++) {
          if (strings[i] === '')
            continue;

          translations[strings[i]] = str_unescape(gt.gettext(str_escape(strings[i])));
        }

        output = JSON.stringify(translations, null, 2);

        fs.writeFileSync("app/l10n/" + lang_code + ".json", output);
      }

      done();
    });
  });

  grunt.registerTask('makeAppData', function() {
    var done = this.async(),
        gt = new Gettext(),
        supported_languages = [];

    gt.setTextDomain('main');

    grunt.file.recurse('pot/', function(absdir, rootdir, subdir, filename) {
      supported_languages.push(filename.replace(/.po$/, ""));
    });

    var appdata = JSON.parse(fs.readFileSync("app/data_src/appdata.json")),
        output = {},
        version = appdata['version'],
        templates = appdata['templates'],
        templates_sources = {};

    var translate_object = function(object, keys) {
      for (var k in keys) {
        if (object[keys[k]]['en'] === '')
          continue;

        supported_languages.forEach(function(lang_code) {
          gt.setLocale(lang_code);
          var translation = gt.gettext(str_escape(object[keys[k]]['en']));
          if (translation !== undefined) {
            object[keys[k]][lang_code] = str_unescape(translation).trim();
          }
        });
      }
    };

    var translate_field = function(field) {
      var i;
      translate_object(field, ['label', 'description', 'hint', 'multi_entry_hint']);

      for (i in field['attrs']) {
        translate_object(field['attrs'][i], ['value']);
      }

      for (i in field['options']) {
        translate_object(field['options'][i], ['label']);
      }

      for (i in field['children']) {
        translate_field(field['children'][i]);
      }
    };

    var translate_step = function(step) {
      translate_object(step, ['label', 'description']);

      for (var c in step['children']) {
        translate_field(step['children'][c]);
      }
    };

    var translate_questionnaire = function(questionnaire) {
      questionnaire['steps'].forEach(function(step) {
        translate_step(step);
      });
    };

    gt.addTranslations("en", 'main', gettextParser.po.parse(fs.readFileSync("pot/en.po")));

    grunt.file.recurse('app/data_src/txt', function(absdir, rootdir, subdir, filename) {
      var template_name = filename.split('.txt')[0],
          filepath = path.join('app/data_src/txt', subdir || '', filename || '');

      templates_sources[template_name] = grunt.file.read(filepath);
    });

    supported_languages.forEach(function(lang_code) {
      gt.setLocale(lang_code);
      gt.addTranslations(lang_code, 'main', gettextParser.po.parse(fs.readFileSync("pot/" + lang_code + ".po")));

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
          if (lines[i] !== '' && !lines[i].match(/^{[a-zA-Z0-9]+}/g)) {
            tmp = tmp.replace(lines[i], str_unescape(translation));
          }
        }

        templates[template_name][lang_code] = tmp.trim();
      }
    });

    output['version'] = version;
    output['templates'] = templates;
    output['node'] = {};

    for (var k in appdata['node']) {
      output['node'][k] = {};
      supported_languages.forEach(function(lang_code) {
        gt.setLocale(lang_code);
        output['node'][k][lang_code] = str_unescape(gt.gettext(str_escape(appdata['node'][k]['en'])));
      });
    }

    output = JSON.stringify(output, null, 2);

    fs.writeFileSync("app/data/appdata.json", output);

    grunt.file.recurse('app/data_src/questionnaires', function(absdir, rootdir, subdir, filename) {
      var srcpath = path.join('app/data_src/questionnaires', subdir || '', filename || '');
      var dstpath = path.join('app/data/questionnaires', subdir || '', filename || '');
      var questionnaire = JSON.parse(fs.readFileSync(srcpath));
      translate_questionnaire(questionnaire);
      fs.writeFileSync(dstpath, JSON.stringify(questionnaire, null, 2));
    });

    grunt.file.recurse('app/data_src/questions', function(absdir, rootdir, subdir, filename) {
      var srcpath = path.join('app/data_src/questions', subdir || '', filename || '');
      var dstpath = path.join('app/data/questions', subdir || '', filename || '');
      var field = JSON.parse(fs.readFileSync(srcpath));
      translate_field(field);
      fs.writeFileSync(dstpath, JSON.stringify(field, null, 2));
    });

    grunt.file.copy('app/data_src/field_attrs.json', 'app/data/field_attrs.json');

    done();
  });

  grunt.registerTask('verifyAppData', function() {
    var app_data = JSON.parse(fs.readFileSync('app/data/appdata.json'));
    var var_map = JSON.parse(fs.readFileSync('app/data/templates_descriptor.json'));

    var failures = [];

    function recordFailure(template_name, lang, text, msg) {
      var line = template_name + " : "+ lang + " : " + msg;
      failures.push(line);
    }

    function checkIfRightTagsUsed(variables, lang, text, template_name, expected_tags) {
      expected_tags.forEach(function(tag) {
        if (text.indexOf(tag) == -1) {
          recordFailure(template_name, lang, text, 'missing expected tag: ' + tag);
        }
      });
    }

    function checkForBrokenTags(variables, lang, text, template_name) {
      var open_b = (text.match(/{/g) || []).length;
      var close_b = (text.match(/{/g) || []).length;

      var tags = text.match(/{[A-Z][a-zA-Z]+}/g) || [];

      if (open_b !== close_b) {
        recordFailure(template_name, lang, text, 'brackets misaligned');
      }
      if (open_b !== tags.length) {
        recordFailure(template_name, lang, text, 'malformed tags');
      }

      // Check to see there are no other commonly used tags inside like: () [] %%, {{}}
      if (text.match(/\([A-Z][a-zA-Z]+\)/g) !== null ||
          text.match(/\[[A-Z][a-zA-Z]+\]/g) !== null ||
          text.match(/%[A-Z][a-zA-Z]+%/g) !== null ||
          text.match(/{{[A-Z][a-zA-Z]+}}/g) !== null) {
        recordFailure(template_name, lang, text, 'mistaken variable tags');
      }

      tags.forEach(function(tag) {
        if (variables.indexOf(tag) < 0) {
          recordFailure(template_name, lang, text, 'invalid tag ' + tag);
        }
      });
    }

    // Check_for_missing_templates
    for (var template_name in var_map) {
      var lang_map = app_data['templates'][template_name]
      var variables = var_map[template_name];
      var expected_tags = (lang_map['en'].match(/{[A-Z][a-zA-Z]+}/g) || []);

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
      console.log('Successfully verified');
    }
  });

  grunt.registerTask('includeExternalFiles', function() {
      fs.writeFileSync('tmp/LICENSE', grunt.file.read('../LICENSE'));
  });

  // Run this task to push translations on transifex
  grunt.registerTask('pushTranslationsSource', ['confirm', '☠☠☠pushTranslationsSource☠☠☠']);

  // Run this task to fetch translations from transifex and create application files
  grunt.registerTask('updateTranslations', ['fetchTranslations', 'makeAppData', 'verifyAppData']);
  // Run this to build your app. You should have run updateTranslations before you do so, if you have changed something in your translations.
  grunt.registerTask('build',
    ['clean', 'copy:sources', 'copy:build', 'includeExternalFiles', 'ngtemplates', 'useminPrepare', 'concat', 'usemin', 'string-replace', 'cleanupWorkingDirectory', 'compress']);

  grunt.registerTask('generateCoverallsJson', function() {
    var done = this.async();
    var coveralls = require('coveralls');

    coveralls.getBaseOptions(function(err, options) {
      if (err) {
        grunt.log.error("Failed to get options, with error: " + err);
        return done(err);
      }

      var fileName = 'coverage/lcov.info';
      fs.readFile(fileName, 'utf8', function(err, fileContent) {
        if (err) {
          grunt.log.error("Failed to read file '" + fileName + "', with error: " + err);
          return done(err);
        }

        coveralls.convertLcovToCoveralls(fileContent, options, function(err, coverallsJson) {
          if (err) {
            grunt.log.error("Failed to convert '" + fileName + "' to coveralls: " + err);
            return done(err);
          }

          // fix file paths so submitting this info with the python coverage works correctly on coveralls.
          if (coverallsJson.source_files) {
            coverallsJson.source_files.forEach(function(srcfile) {
              srcfile.name = "../client/" + srcfile.name;
            });
          }

          var dstpath = 'coverage/coveralls.json';
          fs.writeFileSync(dstpath, JSON.stringify(coverallsJson, null, 2));

          grunt.verbose.ok("Successfully converted " + fileName + " to coveralls json.");
          done();
        });
      });
    });
  });

  grunt.registerTask('end2end-coverage-instrument', [
    'clean',
    'copy:sources',
    'copy:end2end_coverage',
    'instrument'
  ]);

  grunt.registerTask('end2end-coverage-report', [
    'makeReport',
    'generateCoverallsJson'
  ]);
};
