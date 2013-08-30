module.exports = function(grunt) {
  'use strict';
  //
  // Grunt configuration:
  //
  // https://github.com/cowboy/grunt/blob/master/docs/getting_started.md
  //
  grunt.initConfig({

    // compile .scss/.sass to .css using Compass
    // compass: {
    //   dev: {
    //     options: {              // Target options
    //       sassDir: 'app/styles/sass',
    //       cssDir: 'app/styles',
    //       environment: 'development'
    //     }
    //   }
    // },

    // generate application cache manifest
    manifest:{
      dest: 'tmp/'
    },

    // default watch configuration
    watch: {
      files: [
        'app/*.html',
        'app/styles/**/*.scss',
        'app/styles/**/*.css',
        'app/scripts/**/*.js',
        'app/views/**/*.html',
        'app/templates/**/*.html',
        'app/images/**/*'
      ],
      tasks: ['build', 'reload']
    },

    reload: {
        port: 6001,
    },

    // default lint configuration, change this to match your setup:
    // https://github.com/cowboy/grunt/blob/master/docs/task_lint.md#lint-built-in-task
    lint: {
      files: [
        'Gruntfile.js',
        'app/scripts/**/*.js',
        'spec/**/*.js'
      ]
    },

    // specifying JSHint options and globals
    // https://github.com/cowboy/grunt/blob/master/docs/task_lint.md#specifying-jshint-options-and-globals
    jshint: {
      all: ['Gruntfile.js', 'app/scripts/**/*.js'],
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

    // Build configuration
    // -------------------

    clean: {
      release: ['tmp']
    },

    copy: {
        release: {
            files: [{
                dest: 'tmp/', cwd: 'app/', src: ['**'], expand: true
            }]
        }
    },

    // usemin handler should point to the file containing
    // the usemin blocks to be parsed
    'useminPrepare': {
      html: 'tmp/index.html'
    },

    // update references in HTML/CSS to revved files
    usemin: {
      html: ['tmp/templates/**/*.html', 
             'tmp/views/**/*.html',
             'tmp/index.html',
            ],
      css: [
        'tmp/components/bootstrap/docs/assets/css/bootstrap.css',
        'tmp/components/angular-ui/build/angular-ui.css',
        'tmp/components/jquery-file-upload/css/jquery.fileupload-ui.css',
        'tmp/components/jquery-file-upload/css/jquery.fileupload-ui-noscript.css',
        'tmp/styles/**/*.css',
      ],
      options: {
        dirs: ['tmp']
      }
    },

    // HTML minification
    html: {
      files: ['**/*.html']
    },

    // Put all angular.js templates into a single file
    ngtemplates:  {
      GLClient: {
            options: {base: 'app/'},
            src: [ 'app/views/**/*.html', 'app/templates/**/*.html'],
            dest: 'tmp/scripts/templates.js'
          }
    }

  });


  grunt.loadNpmTasks('grunt-usemin');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  // XXX uglification is for the time being disabled since it does not properly
  // work with our codebase.
  // grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-manifest');
  grunt.loadNpmTasks('grunt-angular-templates');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-clean');

  // grunt.loadNpmTasks('grunt-contrib-compass');

  grunt.loadNpmTasks('grunt-reload');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-jshint');

  var path = require('path'),
    superagent = require('superagent'),
    fs = require('fs'),
    Gettext = require("node-gettext"),
    crypto = require('crypto');

  /* grunt.loadNpmTasks('grunt-bower-task'); */

  grunt.registerTask('cleanupWorkingDirectory', function() {
    var images_src = 'tmp/images/**';

    var rm_rf = function(dir) {
      var s = fs.statSync(dir);

      if (!s.isDirectory()) {return fs.unlinkSync(dir);}

      fs.readdirSync(dir).forEach(function(f) {
        rm_rf(path.join(dir || '', f || ''))
      });

      fs.rmdirSync(dir);
    };

    grunt.file.mkdir('build');
    grunt.file.mkdir('build/images');

    grunt.file.copy('tmp/styles.css', 'build/styles.css');
    grunt.file.copy('tmp/scripts.js', 'build/scripts.js');
    grunt.file.copy('tmp/index.html', 'build/index.html');

    grunt.file.recurse('tmp/images', function(absdir, rootdir, subdir, filename) {
        grunt.file.copy(absdir, path.join('build/images', subdir || '', filename || ''));
    });

    rm_rf('tmp');
  });

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
    var url = baseurl + '/resource/glclient-02-enpo/content',
      login = readTransifexrc();

    agent.get(url)
      .auth(login.username, login.password)
      .end(function(err, res){
        var content = JSON.parse(res.text)['content'];
        fs.writeFileSync(sourceFile, content);
        console.log("Written source to " + sourceFile + ".");
        cb();
    });
  }

  function updateTxSource(cb){
    var url = baseurl + '/resource/glclient-02-enpo/content/',
      content = grunt.file.read(sourceFile),
      login = readTransifexrc();

    agent.put(url)
      .auth(login.username, login.password)
      .set('Content-Type', 'application/json')
      .send({'content': content})
      .end(function(err, res){
        console.log(res.text);
        cb();
    });
  }

  function listLanguages(cb){
    var url = baseurl + '/resource/glclient-02-enpo/?details',
      login = readTransifexrc();

    agent.get(url)
      .auth(login.username, login.password)
      .end(function(err, res){
        var result = JSON.parse(res.text);
        cb(result);
    });

  }

  function fetchTxTranslationsForLanguage(langCode, cb) {
    var resourceUrl = baseurl + '/resource/glclient-02-enpo/',
      login = readTransifexrc();

    agent.get(resourceUrl + 'stats/' + langCode + '/')
      .auth(login.username, login.password)
      .end(function(err, res){
        var content = JSON.parse(res.text);

        if (content.translated_entities > content.untranslated_entities) {
          agent.get(resourceUrl + 'translation/' + langCode + '/')
            .auth(login.username, login.password)
            .end(function(err, res){
            var content = JSON.parse(res.text)['content'];
            cb(content);
          });
        } else {
          cb();
        }
      });
  }

  function fetchTxTranslations(cb){
    var fetched_languages = 0,
      total_languages, supported_languages = {};

    listLanguages(function(result){
      total_languages = result.available_languages.length;
      result.available_languages.forEach(function(language){
        var content = grunt.file.read(sourceFile);

        fetchTxTranslationsForLanguage(language.code, function(content){
          if (content) {
            var potFile = "pot/" + language.code + ".po";

            fs.writeFileSync(potFile, content);
            console.log(" { \"code\": \"" + language.code + "\", \"name\": \"" + language.name +"\" },");
            supported_languages[language.code] = language.name;
          }
          fetched_languages += 1;

          if (total_languages == fetched_languages)
            cb(supported_languages);
        });

      });
    });
  }

  grunt.registerTask('pushTx', function(){
    var done = this.async();

    updateTxSource(done);
  });

  grunt.registerTask('pullTx', function(){
    var done = this.async();

    fetchTxTranslations(done);
  });

  grunt.registerTask('updateTranslationsSource', function() {
    var done = this.async(),
      gt = new Gettext(),
      strings,
      translations = {},
      translationStringRegexp = /"(.+?)"\s+\|\s+translate/gi,
      translationStringCount = 0;

    gt.addTextdomain("en");

    function extractPotFromFilepath(filepath) {
      var filecontent = grunt.file.read(filepath),
        result;

      while ( (result = translationStringRegexp.exec(filecontent)) ) {
        gt.setTranslation("en", "", result[1], result[1]);
        translationStringCount += 1;
      }
    };

    grunt.file.recurse('app/templates/', function(absdir, rootdir, subdir, filename) {
        var filepath = path.join('app/templates/', subdir || '', filename || '');
        extractPotFromFilepath(filepath);
    });

    grunt.file.recurse('app/views/', function(absdir, rootdir, subdir, filename) {
        var filepath = path.join('app/views/', subdir || '', filename || '');
        extractPotFromFilepath(filepath);
    });
    extractPotFromFilepath('app/index.html');

    fs.writeFileSync("pot/en.po", gt.compilePO("en"));

    console.log("Written " + translationStringCount + " string to pot/en.po.");
    
    updateTxSource(done);

  });

  grunt.registerTask('makeTranslations', function() {

    var done = this.async(),
      gt = new Gettext(),
      strings,
      translations = {},
      fileContents = fs.readFileSync("pot/en.po"),
      output = "";

    fetchTxTranslations(function(supported_languages){

      gt.addTextdomain("en", fileContents);
      strings = gt.listKeys("en", "");
      translations['supported_languages'] = supported_languages;

      strings.forEach(function(string){
        var md5sum = crypto.createHash('md5'),
          digest;
        md5sum.update(string);
        digest = md5sum.digest('hex');
        translations[digest] = {};

        for (var lang_code in supported_languages) {
          gt.addTextdomain(lang_code, fs.readFileSync("pot/" + lang_code + ".po"));
          translations[digest][lang_code] = gt.dgettext(lang_code, string);
        };
      });

      output += "angular.module('GLClient.translations', []).factory('Translations', function() { return ";
      output += JSON.stringify(translations);
      output += "});\n";

      fs.writeFileSync("app/scripts/translations.js", output);

      console.log("Translations file was written!");

      });

  });

  // Run this task to update translation related files
  grunt.registerTask('updateTranslations', ['updateTranslationsSource', 'makeTranslations']);

  // Run this to build your app. You should have run updateTranslations before you do so, if you have changed something in your translations.
  grunt.registerTask('build',
    ['clean', 'copy', 'ngtemplates', 'useminPrepare', 'concat', 'usemin', 'manifest', 'cleanupWorkingDirectory']);

  // XXX disabled uglify
  // ['clean', 'useminPrepare', 'copy', 'ngtemplates', 'concat', 'uglify', 'usemin', 'manifest']);
  grunt.registerTask('dev',
    ['reload', 'watch']);
};
