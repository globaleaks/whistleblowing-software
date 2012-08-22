/**
 * A simple server that can serve up the UI in dev
 *
 * Runs the dev code: devserver.js docRoot=../www
 *
 * Valid options are:
 *
 * docRoot= the directory to use as the document root. By default it uses the
 * current working directory.
 *
 * host=127.0.0.1 the host to use in the connection. By default it uses
 * 127.0.0.1 so it is only visible to the computer running the server, but
 * if you use 0.0.0.0 it may be visible to more servers on your network.
 *
 * port=8360 the port to use. Default is 8360
 */

/*jslint node: true */
/*global define, console */
'use strict';

//Command line args are of the form name=value
function makeOptions() {
    var args = process.argv.slice(2),
        options = {};
    args.forEach(function (arg) {
        var index = arg.indexOf('=');
        options[arg.substring(0, index)] = arg.substring(index + 1);
    });

    return options;
}

var http = require('http'),
    https = require('https'),
    fs = require('fs'),
    path = require('path'),
    url = require('url'),
    queryString = require('querystring'),
    options = makeOptions(),
    docRoot = path.resolve(options.docRoot),
    host = options.host || '127.0.0.1',
    port = options.port || 8360,
    server, apiHandlers, mimeTypes, utf8Types;

mimeTypes = {
    'appcache': 'text/cache-manifest',
    'css': 'text/css',
    'f4v': 'video/x-f4v',
    'fli': 'video/x-fli',
    'flv': 'video/x-flv',
    'fvt': 'video/vnd.fvt',
    'gif': 'image/gif',
    'h264': 'video/h264',
    'html': 'text/html',
    'ico': 'image/x-icon',
    'jpg': 'image/jpeg',
    'js': 'application/javascript',
    'json': 'application/json',
    'm1v': 'video/mpeg',
    'm2v': 'video/mpeg',
    'm4u': 'video/vnd.mpegurl',
    'm4v': 'video/mp4',
    'mov': 'video/quicktime',
    'mp4': 'video/mp4',
    'mp4v': 'video/mp4',
    'mpe': 'video/mpeg',
    'mpeg': 'video/mpeg',
    'mpg': 'video/mpeg',
    'mpg4': 'video/mp4',
    'mxu': 'video/vnd.mpegurl',
    'ogv': 'video/ogg',
    'png': 'image/png',
    'qt': 'video/quicktime',
    'txt': 'text/plain',
    'webapp': 'application/x-web-app-manifest+json',
    'webm': 'video/webm',
    'xml': 'application/xml'
};

utf8Types = {
    'appcache': true,
    'css': true,
    'html': true,
    'js': true,
    'json': true,
    'xml': true
};

function sendError(res, code, message) {
    res.writeHead(code);
    res.end((message || '').toString());
}

function handleRequest(req, res) {
    var host = req.headers.host,
        hostParts = host.split('.'),
        subdomain = hostParts[0],
        urlPath, stream, ext, stat, mimeType;

    if (req.method === 'GET') {
        // A static file to serve. Only handle GETs
        urlPath = req.url;
        urlPath = path.normalize(urlPath);
        // Trim off leading slash now.
        urlPath = urlPath.substring(1);

        // Do not allow paths outside of docRoot
        if (urlPath.indexOf('.') === 0) {
            sendError(res, 500, 'invalid path: ' + urlPath);
            return;
        }

        urlPath = path.resolve(docRoot, urlPath);

        if (!urlPath || !path.existsSync(urlPath)) {
            sendError(res, 404);
            return;
        }

        stat = fs.statSync(urlPath);

        // Look for an index.html if this is a directory.
        if (stat.isDirectory()) {
            urlPath = path.join(urlPath, 'index.html');
            if (!path.existsSync(urlPath)) {
                sendError(res, 404);
                return;
            }
            stat = fs.statSync(urlPath);
        }

        // Grab the file extension, and since extname returns
        // the dot in the value, strip off the dot. Then get mime
        // type.
        ext = path.extname(urlPath).substring(1);
        mimeType = mimeTypes[ext] || 'text/plain';

        // Set up headers. Do not send any caching headers, because
        // this is for dev, so want fresh sends each request.
        res.setHeader('Content-Type', mimeType +
                      (utf8Types[ext] ? '; charset=utf-8' : ''));
        res.setHeader('Content-Length', stat.size);

        // Start streaming back the contents.
        stream = fs.createReadStream(urlPath);
        stream.pipe(res);
    } else {
        sendError(res, 500);
    }
}


server = http.createServer(handleRequest);
server.listen(port, host);

console.log('Using ' + docRoot + ' for: http://' + host + ':' + port +
            '\nUse CTRL+C to kill the server.');
