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
      html: ['tmp/**/*.html'],
      css: ['tmp/**/*.css'],
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

  /* grunt.loadNpmTasks('grunt-bower-task'); */

  grunt.registerTask('cleanupWorkingDirectory', function() {
    var path = require('path'),
      fs = require('fs'),
      images_src = 'tmp/images/**';

    var rm_rf = function(dir) {
      var s = fs.statSync(dir);

      if (!s.isDirectory()) {return fs.unlinkSync(dir);}

      fs.readdirSync(dir).forEach(function (f) {
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

  grunt.registerTask('makeTranslations', function() {
    var Gettext = require("node-gettext"),
      fs = require('fs'),
      crypto = require('crypto'),
      gt = new Gettext(),
      strings,
      translations = {},
      fileContents = fs.readFileSync("pot/en.po"),
      supported_languages = {'en': 'English', 'de': 'German',
                             'el': 'Greek', 'hu': 'Hungarian',
                             'it': 'Italian', 'nl': 'Dutch',
                             'pl': 'Polish'};

    translations['supported_languages'] = supported_languages;

    gt.addTextdomain("en", fileContents);
    strings = gt.listKeys("en", "");

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

    fs.writeFile("app/scripts/translations.js", "var translations = " + JSON.stringify(translations) + ";",
                 function(err) {
      if (err) console.log(err);
      else console.log("Translsations file was written!");
    });
  });

  grunt.registerTask('build',
    ['clean', 'makeTranslations', 'copy', 'ngtemplates', 'useminPrepare', 'concat', 'usemin', 'manifest', 'cleanupWorkingDirectory']);

  // XXX disabled uglify
  // ['clean', 'useminPrepare', 'copy', 'ngtemplates', 'concat', 'uglify', 'usemin', 'manifest']);
  grunt.registerTask('dev',
    ['reload', 'watch']);
};
