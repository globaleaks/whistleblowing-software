/*global window */

define(function (require) {
    'use strict';

    var $ = require('jquery'),
        hasher = require('hasher'),
        crossroads = require('crossroads');
    require('datatables');

    require('datatables.bootstrap');

    return function myFunc(parentDom) {
        var tip_el = $("#tipListTableBody");

        for (var i = 0;i < 120;i++) {
            var klass = (i % 2 == 0) ? 'even' : 'odd';

            // XXX This is just some random junk data
            var name = "Antani Sblinda",
                views = Math.round(Math.random()*1000)*3,
                diff = Math.round(Math.random()*10);

            var date = new Date();
            date.setDate(-1*diff*100);

            var my_views = views - Math.round(diff/2);
            var downloads = views - Math.round(diff/4);
            var pertinence = diff;

            var row = '<tr class="'+klass+'">';
            row += '<td>'+name+'</td>';
            row += '<td>'+date+'</td>';
            row += '<td>'+my_views+'</td>';
            row += '<td>'+views+'</td>';
            row += '<td>'+downloads+'</td>';
            row += '<td>'+pertinence+'</td>';
            row += '</tr>';
            tip_el.append(row);
        }
        $('#tipList').dataTable( {
            "sDom": "<'row'<'span4'l><'span5'f>r>t<'row'<'span4'i><'span5'p>>",
            "sPaginationType": "bootstrap",
            "oLanguage": {
                "sLengthMenu": "_MENU_ records per page"
            }

        });

        parentDom = parentDom || $('body');
    };
});
