// This is used to build the app and compact it
({
    appDir: "../",
    baseUrl: "js",
    dir: "../build",
    paths: {
        jquery: 'libs/jquery/jquery-min',
        underscore: 'libs/underscore/underscore-min',
        backbone: 'libs/backbone/backbone-optamd3-min',
        text: 'libs/require/text',
        templates: '../templates'
    },
    modules: [
        {
            name: "main"
        }
    ]
})
