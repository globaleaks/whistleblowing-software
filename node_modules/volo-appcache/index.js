
/*jslint node: true, nomen: true */
'use strict';

/**package
{
    "name": "volo-appcache",
    "description": "A volo command for generating an appcache manifest",
    "keywords": [
        "volo"
    ],
    "version": "0.0.1",
    "homepage": "http://github.com/volojs/volo-appcache",
    "author": "James Burke <jrburke@gmail.com> (http://github.com/jrburke)",
    "licenses": [
        {
            "type": "BSD",
            "url": "https://github.com/volojs/volo-ghdeploy/blob/master/LICENSE"
        },
        {
            "type": "MIT",
            "url": "https://github.com/volojs/volo-ghdeploy/blob/master/LICENSE"
        }
    ],
    "engines": {
        "node": ">=0.6.7"
    }
}
**/

var fs = require('fs'),
    crypto = require('crypto');

function generateDigest(q, files, dir) {

    var masterDeferred = q.defer(),
        digests = [],
        i = 0;

    function getDigest(fileName) {
        var shaSum = crypto.createHash('sha1'),
            d = q.defer(),
            stream = fs.ReadStream(fileName);

        stream.on('data', function (data) {
            shaSum.update(data);
        });

        stream.on('end', function () {
            d.resolve(shaSum.digest('base64'));
        });

        return d.promise;
    }

    function digestFile(fileName) {
        getDigest(fileName).then(function (digest) {
            var shaSum;

            digests[i] = digest;
            i += 1;

            if (i < files.length) {
                digestFile(files[i]);
            } else {
                //All done, now generate the final digest,
                //using the combination of the other digests
                shaSum = crypto.createHash('sha1');
                shaSum.update(digests.join(','));
                masterDeferred.resolve(shaSum.digest('base64'));
            }
        });
    }

    digestFile(files[0]);

    return masterDeferred.promise;
}

/**
 * Returns a volo command that is wired up to use the given
 * directory to generate a manifest.
 *
 * @param {Object} options, where the allowed options are:
 *
 *     @param {Array} depends: a set of volo commands this command should
 *     depend on. Default is empty.
 *
 *     @param  {String} dir the directory that has the contents that should
 *     be included in the manifest. Default is 'www-built'
 *
 *     @param  {Sting} htmlPath the path to the file inside the "dir" directory
 *     that is an HTML file that should get the "manifest" attribute inserted in
 *     its HTML tag. Default is 'index.html'.
 *
 *     @param {String} manifestTemplate the path to a template to use for the
 *     manifest. Defaults to the manifest.template in the directory housing
 *     this module. Note that the template contains some tokens replaced
 *     by this command.
 *
 * @return {Object} The volo command.
 */
module.exports = function (options) {
    //Set up defaults
    var dir = options.dir || 'www-built',
        htmlPath = options.htmlPath || 'index.html',
        manifestTemplate = options.manifestTemplate ||
                           __dirname + '/manifest.template',
        trailingChar = dir.charAt(dir.length - 1);

    //Make sure dir does not have a trailing slash
    if (trailingChar === '/' || trailingChar === '\\') {
        dir = dir.substring(0, dir.length - 1);
    }

    //Return an object that conforms to the volo command API.
    return {
        summary: 'Generates the manifest.appcache file for ' + dir + ' and ' +
            'modifies ' + htmlPath + ' to add the "manifest" attribute to ' +
            'the <html> tag.',

        depends: options.depends,

        run: function (d, v, namedArgs) {
            if (!v.exists(dir)) {
                d.reject(dir + ' does not exist');
                return;
            }

            try {
                var q = v.require('q'),
                    manifest = v.read(manifestTemplate),
                    master = v.read(dir + '/' + htmlPath),
                    fullFilePaths,
                    appFiles;

                fullFilePaths = v.getFilteredFileList(dir, null, /\.htaccess/);
                appFiles = fullFilePaths.map(function (file) {
                    var start = file.indexOf('/' + dir + '/');
                    start = (start !== -1) ? (start + 11) : 0;
                    return file.substr(start, file.length);
                });

                master = master
                        .replace(/<html\s?/, '<html manifest="manifest.appcache" ')
                        .replace(/manifest\.appcache"\s>/, 'manifest.appcache">');
                v.write(dir + '/' + htmlPath, master);

                generateDigest(q, fullFilePaths, dir).then(function (stamp) {
                    manifest = v.template(manifest, {
                        files : appFiles.join('\n'),
                        stamp : stamp
                    });
                    v.write(dir + '/manifest.appcache', manifest);
                }).then(d.resolve, d.reject);
            } catch (e) {
                d.reject(e);
            }
        }
    };
};
