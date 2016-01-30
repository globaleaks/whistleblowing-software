module.exports = function(grunt) {
  grunt.initConfig({
    manifest:{
      dest: 'tmp/'
    },

    bower: {
      install: {
        options: {
          copy: false
        }
      }
    },

    lint: {
      files: ['Gruntfile.js', 'app/js/**/*.js'],
    },

    jshint: {
      all: ['Gruntfile.js', 'app/js/**/*.js'],
      options: {
        curly: true,
        eqeqeq: true,
        immed: true,
        latedef: true,
        newcap: true,
        noarg: true,
        sub: true,
        undef: true,
        boss: true,
        eqnull: true,
        browser: true
      },
      globals: {
        angular: true
      }
    },

    clean: {
      build: ['tmp', 'build']
    },

    copy: {
      build: {
          files: [{
            dest: 'tmp/', cwd: 'app/', src: ['**'], expand: true
          }]
      },
      end2end_coverage: {
          files: [{
            dest: 'build/',
            cwd: 'app/',
            src: [
              '**',
              '!js/**/*.js', // Don't copy scripts that will be instrumented.
              'js/crypto/**/*.js' // Copy scripts that should not be instrumented.
            ],
            expand: true
          }]
      }
    },

    useminPrepare: {
      html: [
        'tmp/index.html',
        'tmp/app.html',
      ],
      options: {
        staging: 'tmp',
        dest: 'tmp',
        flow: {
          steps: {
            js: ['concat'], // we avoid to minify intentionally! #1417 !
            css: ['concat', 'cssmin']
          },
          post: {}
        }
      }
    },

    usemin: {
      html: [
        'tmp/index.html',
        'tmp/app.html',
        'tmp/views/**/*.html'
      ],
      options: {
        dirs: ['tmp']
      }
    },

    html: {
      files: ['**/*.html']
    },

    inline: {
        build: {
            options:{
                tag: 'inline'
            },
            src: 'tmp/index.html',
            dest: 'tmp/index.html'
        }
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

    protractor: {
      options: {
        keepAlive: true,
        noColor: false,
        singleRun: true
      },
      test: {
        configFile: "tests/end2end/protractor.config.js"
      },
      saucelabs: {
        configFile: "tests/end2end/protractor-sauce.config.js",
        options: {
          build: process.env.TRAVIS_BUILD_NUMBER
        }
      }
    },

    'string-replace': {
      inline: {
        files: {
          'tmp/index.html': 'tmp/index.html'
        },
        options: {
          replacements: [
            {
              pattern: '<link rel="stylesheet" href="css/styles.css">',
              replacement: '<link rel="stylesheet" data-ng-href="{{app_stylesheet}}">'
            },
            {
              pattern: '<script src="js/scripts.js"></script>',
              replacement: ''
            },
            {
              pattern: '<!-- start_globaleaks(); -->',
              replacement: 'start_globaleaks();'
            }
          ]
        }
      }
    },

    confirm: {
      updateTranslations: {
        options: {
          // Static text.
          question: 'WARNING:\n'+
                    'this task may cause translations loss and should be executed only on master branch.\n\n' +
                    'Are you sure you want to proceed (Y/N)?',
          continue: function(answer) {
            return answer === 'Y';
          }
        }
      }
    },

    instrument: {
      files: 'js/**/*.js',
      options: {
        lazy: true,
        cwd: 'app/',
        basePath: 'build'
      }
    },
    protractor_coverage: {
      options: {
        keepAlive: true,
        noColor: false,
        coverageDir: 'coverage'
      },
      local: {
        options: {
          configFile: 'tests/end2end/protractor-coverage.config.js'
        }
      }
    },
    makeReport: {
      src: 'coverage/coverage*.json',
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
  grunt.loadNpmTasks('grunt-bower-task');
  grunt.loadNpmTasks('grunt-confirm');
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-connect');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-istanbul');
  grunt.loadNpmTasks('grunt-inline-alt');
  grunt.loadNpmTasks('grunt-istanbul');
  grunt.loadNpmTasks('grunt-line-remover');
  grunt.loadNpmTasks('grunt-manifest');
  grunt.loadNpmTasks('grunt-protractor-coverage');
  grunt.loadNpmTasks('grunt-protractor-runner');
  grunt.loadNpmTasks('grunt-string-replace');
  grunt.loadNpmTasks('grunt-usemin');

  var readDynamicStrings = function() {
    var filecontent = grunt.file.read('app/data_src/dynamic_strings.json'),

    ret = {};
    ret['mapping'] = JSON.parse(filecontent);
    ret['inverse_mapping'] = {}
    for (var key in ret['mapping']) {
      ret['inverse_mapping'][(ret['mapping'][key])] = key;
    };

    return ret;
  }

  var readNoTranslateStrings = function() {
    return JSON.parse(grunt.file.read('app/data_src/notranslate_strings.json'));
  }

  var path = require('path'),
    superagent = require('superagent'),
    fs = require('fs'),
    Gettext = require("node-gettext"),
    dynamic_strings = readDynamicStrings(),
    notranslate_strings = readNoTranslateStrings()

  grunt.registerTask('copyBowerSources', function() {
    var files = [
      ['app/components/bootstrap/dist/css/bootstrap.min.css', 'app/css/bootstrap.min.css'],
      ['app/components/bootstrap-rtl-ondemand/dist/css/bootstrap-rtl-ondemand.min.css', 'app/css/bootstrap-rtl-ondemand.min.css'],
      ['app/components/scrypt-async/scrypt-async.min.js', 'app/js/crypto/scrypt-async.min.js'],
      ['app/components/openpgp/dist/openpgp.min.js', 'app/js/crypto/openpgp.min.js'],
      ['app/components/openpgp/dist/openpgp.worker.min.js', 'app/js/crypto/openpgp.worker.min.js']
    ]

    grunt.file.mkdir('app/js/crypto');

    for (var x in files) {
        grunt.file.copy(files[x][0], files[x][1])
    }

    grunt.file.recurse('app/components/bootstrap/fonts', function(absdir, rootdir, subdir, filename) {
      grunt.file.copy(absdir, path.join('app/fonts', subdir || '', filename || ''));
    });
  });

  grunt.registerTask('cleanupWorkingDirectory', function() {
    var rm_rf = function(dir) {
      var s = fs.statSync(dir);

      if (!s.isDirectory()) {return fs.unlinkSync(dir);}

      fs.readdirSync(dir).forEach(function(f) {
        rm_rf(path.join(dir || '', f || ''))
      });

      fs.rmdirSync(dir);
    };

    grunt.file.mkdir('build/');

    var files = ['index.html', 'index.js', 'app.html']
    for (var x in files) {
      grunt.file.copy('tmp/' + files[x], 'build/' + files[x]);
    }

    grunt.file.copy('tmp/css/styles.css', 'build/css/styles.css');
    grunt.file.copy('tmp/js/scripts.js', 'build/js/scripts.js');
    grunt.file.copy('tmp/js/plugin.js', 'build/js/plugin.js');

    var dirs = ['js/crypto']
    for (var x in dirs) {
      grunt.file.recurse('tmp/' + dirs[x], function(absdir, rootdir, subdir, filename) {
        grunt.file.copy(absdir, path.join('build/' + dirs[x], subdir || '', filename || ''));
      });
    }

    var dirs = ['fonts', 'l10n', 'data']
    for (var x in dirs) {
      grunt.file.recurse('tmp/' + dirs[x], function(absdir, rootdir, subdir, filename) {
        grunt.file.copy(absdir, path.join('build/' + dirs[x], subdir || '', filename || ''));
      });
    }

    rm_rf('tmp');
  });

  function str_escape (val) {
      if (typeof(val)!="string") return val;
      return val
        .replace(/[\n]/g, '\\n')
        .replace(/[\t]/g, '\\r');
  }

  function str_unescape (val) {
      if (typeof(val)!="string") return val;
      return val
        .replace(/\\n/g, '\n')
        .replace(/\\t/g, '\t');
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
    baseurl = 'http://www.transifex.com/api/2/project/globaleaks',
    sourceFile = 'pot/en.po';

  function fetchTxSource(cb){
    var url = baseurl + '/resource/master/content',
      login = readTransifexrc();

    agent.get(url)
      .auth(login.username, login.password)
      .end(function(err, res){
        if (res.ok) {
          var content = JSON.parse(res.text)['content'];
          fs.writeFileSync(sourceFile, content);
          console.log("Written source to " + sourceFile + ".");
          cb();
        } else {
          console.log('Error: ' + res.text);
        }
    });
  }

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
          console.log('Error: failed to fetch resource ' + url);
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
                      var content = JSON.parse(res.text)['content'];
                      cb(content);
                    } else {
                      console.log('Error: ' + res.text);
                    }
                  } else {
                    console.log('Error: failed to fetch resource ' + url);
                  }
              });
            } else {
              cb();
            }
          } else {
            console.log('Error: ' + res.text);
          }
        } else {
          console.log('Error: failed to fetch resource ' + url);
        }
      })
  }

  function fetchTxTranslations(cb){
    var fetched_languages = 0,
      total_languages, supported_languages = {};

    listLanguages(function(result){
      result.available_languages = result.available_languages.filter(function( language ) {
        /*
            we skip en_US that is used internaly only as feedback in order
            to keep track of corrections suggestions
        */
        return language.code !== 'en_US';
      });

      total_languages = result.available_languages.length;

      result.available_languages.forEach(function(language){

        var content = grunt.file.read(sourceFile);

        fetchTxTranslationsForLanguage(language.code, function(content){
          if (content) {
            var potFile = "pot/" + language.code + ".po";

            fs.writeFileSync(potFile, content);
            console.log("Fetched " + language.code);
            supported_languages[language.code] = language.name;
          }

          fetched_languages += 1;

          if (total_languages == fetched_languages) {
            var sorted_keys = Object.keys(supported_languages).sort();

            console.log("List of available translations:");

            for (var i in sorted_keys) {
              console.log(" { \"code\": \"" + sorted_keys[i] +
                          "\", \"name\": \"" + supported_languages[sorted_keys[i]] +"\" },");
            }

            cb(supported_languages);
          }
        });

      });
    });
  }

  grunt.registerTask('updateTranslationsSource', function() {
    var done = this.async(),
      gt = new Gettext(),
      strings,
      translations = {},
      translationStringRegexpHTML1 = /"(.+?)"\s+\|\s+translate/gi,
      translationStringRegexpHTML2 = /translate>(.+?)</gi,
      translationStringRegexpJSON = /"en": "(.+)"/gi,
      translationStringCount = 0;

    gt.addTextdomain("en");

    function addString(str) {
      if (notranslate_strings.indexOf(str) !== -1)
        return;

      if (str in dynamic_strings['mapping']) {
        str = dynamic_strings['mapping'][str];
        gt.setTranslation("en", "", str, str);
      } else {
        gt.setTranslation("en", "", str, str);
      }

      translationStringCount += 1;
    };

    function extractPOFromHTMLFile(filepath) {
      var filecontent = grunt.file.read(filepath),
        result;

      while (result = translationStringRegexpHTML1.exec(filecontent)) {
        addString(result[1]);
      }

      while (result = translationStringRegexpHTML2.exec(filecontent)) {
        addString(result[1]);
      }

    };

    function extractPOFromJSONFile(filepath) {
      var filecontent = grunt.file.read(filepath),
        result;

      while (result = translationStringRegexpJSON.exec(filecontent)) {
        addString(result[1]);
      }
    };

    function extractPOFromTXTFile(filepath) {
      var filecontent = grunt.file.read(filepath),
          lines = filecontent.split("\n"),
          result;

      for (var i=0; i<lines.length; i++){
        // we skip adding empty strings and variable only strings
        if (lines[i] != '' && !lines[i].match(/^%[a-zA-Z0-9]+%/g)) {
          addString(lines[i]);
        }
      }
    };

    extractPOFromHTMLFile('app/app.html');

    /* Extract strings view file used to anticipate strings on transifex */
    extractPOFromHTMLFile('app/translations.html');

    grunt.file.recurse('app/views/', function(absdir, rootdir, subdir, filename) {
      var filepath = path.join('app/views/', subdir || '', filename || '');
      extractPOFromHTMLFile(filepath);
    });

    grunt.file.recurse('app/data_src/txt', function(absdir, rootdir, subdir, filename) {
      var filepath = path.join('app/data_src/txt', subdir || '', filename || '');
      extractPOFromTXTFile(filepath);
    });

    grunt.file.recurse('app/data_src/fields', function(absdir, rootdir, subdir, filename) {
      var filepath = path.join('app/data_src/fields', subdir || '', filename || '');
      extractPOFromJSONFile(filepath);
    });

    extractPOFromJSONFile('app/data_src/appdata.json');

    grunt.file.mkdir("pot");

    fs.writeFileSync("pot/en.po", gt.compilePO("en"));

    console.log("Written " + translationStringCount + " string to pot/en.po.");

    updateTxSource(done);
  });

  grunt.registerTask('makeTranslations', function() {
    var done = this.async(),
      gt = new Gettext(),
      strings,
      fileContents = fs.readFileSync("pot/en.po");

    function addTranslation(translations, key, value) {
      if (key in dynamic_strings['inverse_mapping']) {
        key = dynamic_strings['inverse_mapping'][key];
      }

      translations[key] = value;
    };

    fetchTxTranslations(function(supported_languages){

      gt.addTextdomain("en", fileContents);
      strings = gt.listKeys("en", "");

      for (var lang_code in supported_languages) {
        var translations = {}, output;

        strings.forEach(function(string){
          gt.addTextdomain(lang_code, fs.readFileSync("pot/" + lang_code + ".po"));
          addTranslation(translations, string, str_unescape(gt.dgettext(lang_code, str_escape(string))));
        });

        output = JSON.stringify(translations);

        fs.writeFileSync("app/l10n/" + lang_code + ".json", output);

      }

      done();

    });
  });

  grunt.registerTask('makeAppData', function() {
    var done = this.async(),
      gt = new Gettext(),
      strings,
      fileContents = fs.readFileSync("pot/en.po");

    fetchTxTranslations(function(supported_languages){
      var json = JSON.parse(fs.readFileSync("app/data_src/appdata.json")),
          output = {},
          version = json['version'],
          default_questionnaire = json['default_questionnaire'],
          templates = json['templates'],
          templates_sources = {};

      var translate_model = function(object, keys) {
        for (var k in keys) {
          for (var lang_code in supported_languages) {
            object[keys[k]][lang_code] = str_unescape(gt.dgettext(lang_code, str_escape(object[keys[k]]['en'])));
          }
        }
      }

      var translate_fieldattr = function(fieldattr) {
        if (fieldattr['type'] == 'localized') {
          for (var lang_code in supported_languages) {
            fieldattr['value'][lang_code] = str_unescape(gt.dgettext(lang_code, str_escape(fieldattr['value']['en'])));
          }
        }
      }

      var translate_field = function(field) {
        translate_model(field, ['label', 'description', 'hint', 'multi_entry_hint']);

        for (var i in field['attrs']) {
          translate_fieldattr(field['attrs'][i]);
        }

        for (var c in field['children']) {
          translate_field(field['children'][c]);
        }
      }

      var translate_step = function(step) {
        translate_model(step, ['label', 'description']);

        for (var c in step['children']) {
          translate_field(step['children'][c]);
        }
      }

      var translate_questionnaire = function(questionnaire) {
        for (var s in questionnaire) {
          translate_step(questionnaire[s]);
        };
      }

      gt.addTextdomain("en", fileContents);

      for (var lang_code in supported_languages) {
        gt.addTextdomain(lang_code, fs.readFileSync("pot/" + lang_code + ".po"));
      }

      grunt.file.recurse('app/data_src/txt', function(absdir, rootdir, subdir, filename) {
        var template_name = filename.split('.txt')[0],
            filepath = path.join('app/data_src/txt', subdir || '', filename || ''),
            result;

        templates_sources[template_name] = grunt.file.read(filepath);
      });

      for (var lang_code in supported_languages) {
        for (var template_name in templates_sources) {
          if (!(template_name in templates)) {
            templates[template_name] = {}
          }

          var tmp = templates_sources[template_name];

          var lines = templates_sources[template_name].split("\n");

          for (var i=0; i<lines.length; i++){

            // we skip adding empty strings and variable only strings
            if (lines[i] != '' && !lines[i].match(/^%[a-zA-Z0-9]+%/g)) {
              tmp = tmp.replace(lines[i], str_unescape(gt.dgettext(lang_code, str_escape(lines[i]))));
            }
          }

          templates[template_name][lang_code] = tmp;
        }
      };

      output['version'] = version;
      output['default_questionnaire'] = default_questionnaire;
      output['templates'] = templates;
      output['node'] = {};

      for (var k in json['node']) {
        output['node'][k] = {};
        for (var lang_code in supported_languages) {
          output['node'][k][lang_code] = str_unescape(gt.dgettext(lang_code, str_escape(json['node'][k]['en'])));
        };
      };

      translate_questionnaire(output['default_questionnaire']);

      output = JSON.stringify(output);

      fs.writeFileSync("app/data/appdata.json", output);

      grunt.file.recurse('app/data_src/fields', function(absdir, rootdir, subdir, filename) {
        var srcpath = path.join('app/data_src/fields', subdir || '', filename || '');
        var dstpath = path.join('app/data/fields', subdir || '', filename || '');
        var field = JSON.parse(fs.readFileSync(srcpath));
        translate_field(field);
        field = JSON.stringify(field);
        fs.writeFileSync(dstpath, field);
      });

      console.log("Fields file was written!");

      done();
    });

  });

  grunt.registerTask('setupDependencies', ['bower:install', 'copyBowerSources']);

  // Run this task to update translation related files
  grunt.registerTask('updateTranslations', ['confirm', 'updateTranslationsSource', 'makeTranslations', 'makeAppData']);

  // Run this to build your app. You should have run updateTranslations before you do so, if you have changed something in your translations.
  grunt.registerTask('build',
    ['clean:build', 'copy:build', 'ngtemplates', 'useminPrepare', 'concat', 'cssmin', 'usemin', 'string-replace', 'inline', 'manifest', 'cleanupWorkingDirectory']);

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
          fs.writeFileSync(dstpath, JSON.stringify(coverallsJson));

          grunt.verbose.ok("Successfully converted " + fileName + " to coveralls json.");
          done();
        });
      });
    });
  });

  grunt.registerTask('end2end-coverage', [
    'clean:build',
    'copy:end2end_coverage',
    'instrument',
    'protractor_coverage:local',
    'makeReport',
    'generateCoverallsJson'
  ]);
};
