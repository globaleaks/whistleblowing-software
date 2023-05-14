GL.controller("FeaturesCtrl", ["$scope",
    function ($scope) {
        $scope.search = undefined;
        $scope.currentPage = 1;
        $scope.itemsPerPage = 20;
        $scope.dropdownSettings = { dynamicTitle: false, showCheckAll: false, showUncheckAll: false, enableSearch: true, displayProp: "label", idProp: "label", itemsShowLimit: 5 };

        $scope.reportDateFilter = null;
        $scope.updateDateFilter = null;
        $scope.expiryDateFilter = null;

        $scope.dropdownStatusModel = [];
        $scope.dropdownStatusData = [];
        $scope.dropdownContextModel = [];
        $scope.dropdownContextData = [];
        $scope.dropdownScoreModel = [];
        $scope.dropdownScoreData = [];

        var uniqueKeys = [];

        angular.forEach($scope.resources.rtips.rtips, function (tip) {
            tip.context = $scope.contexts_by_id[tip.context_id];
            tip.context_name = tip.context.name;
            tip.questionnaire = $scope.resources.rtips.questionnaires[tip.questionnaire];
            tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText(tip.status, tip.substatus, $scope.submission_statuses);

            if (!uniqueKeys.includes(tip.submissionStatusStr)) {
                uniqueKeys.push(tip.submissionStatusStr);
                $scope.dropdownStatusData.push({ id: $scope.dropdownStatusData.length + 1, label: tip.submissionStatusStr });
            }

            if (!uniqueKeys.includes(tip.context_name)) {
                uniqueKeys.push(tip.context_name);
                $scope.dropdownContextData.push({ id: $scope.dropdownContextData.length + 1, label: tip.context_name });
            }

            var scoreLabel = $scope.Utils.maskScore(tip.score);

            if (!uniqueKeys.includes(scoreLabel)) {
                uniqueKeys.push(scoreLabel);
                $scope.dropdownScoreData.push({ id: $scope.dropdownScoreData.length + 1, label: scoreLabel });
            }
        });

        $scope.reports = $scope.resources.rtips.rtips;
        $scope.totalReports = $scope.resources.rtips.rtips.length;
        $scope.submissionStatuses = $scope.submission_statuses;

        $scope.substatusPercentage = function (status, substatus) {
            var substatusesCount = status.substatuses.length;
            var substatusCount = substatusesCount > 0 ? 1 : 0;
            var substatusPercentage = (substatusCount / substatusesCount) * 100;
            return substatusPercentage.toFixed(2);
        };

        $scope.statusPercentage = function (status) {
            var statusesCount = $scope.submissionStatuses.length;
            var statusCount = 1;
            var statusPercentage = (statusCount / statusesCount) * 100;
            return statusPercentage.toFixed(2);
        };

        $scope.statusCount = function (status) {
            return status.substatuses.length + 1;
        };

        $scope.data = $scope.resources.rtips.rtips;
        $scope.labelCounts = {};
        $scope.unlabeledCount = 0;

        $scope.calculateCounts = function () {
            angular.forEach($scope.data, function (item) {
                var label = item.label;

                if (label) {
                    if ($scope.labelCounts[label
                    ]) {
                        $scope.labelCounts[label]++;
                    } else {
                        $scope.labelCounts[label] = 1;
                    }
                } else {
                    $scope.unlabeledCount++;
                }
            });

            var totalItemCount = $scope.data.length;

            angular.forEach($scope.labelCounts, function (count, label) {
                var percentage = (count / totalItemCount) * 100;
                $scope.labelCounts[label] = {
                    count: count,
                    percentage: percentage.toFixed(2) + "%"
                };
            });

            var unlabeledPercentage = ($scope.unlabeledCount / totalItemCount) * 100;
            $scope.unlabeledCount = {
                count: $scope.unlabeledCount,
                percentage: unlabeledPercentage.toFixed(2) + "%"
            };
        };

        $scope.calculateCounts();

        var recipientActions = $scope.resources.rtips.rtips;
        var totalDiffInMilliseconds = 0;

        for (var i = 0; i < recipientActions.length; i++) {
            var expirationDate = new Date(recipientActions[i].expiration_date);
            var updateDate = new Date(recipientActions[i].update_date);
            var creationDate = new Date(recipientActions[i].creation_date);

            var updateDiffInMilliseconds = updateDate.getTime() - creationDate.getTime();
            var expirationDiffInMilliseconds = expirationDate.getTime() - creationDate.getTime();

            totalDiffInMilliseconds += (updateDiffInMilliseconds + expirationDiffInMilliseconds);
        }

        var averageDiffInMilliseconds = totalDiffInMilliseconds / (2 * recipientActions.length);
        var averageDiffInDay = averageDiffInMilliseconds / (1000 * 60 * 60 * 24);

        $scope.averageDiffInDays = averageDiffInDay.toFixed(2);

        // var submissions = $scope.resources.rtips.rtips;
        // var totalDiffInMilliseconds = 0;
        // var numClosedSubmissions = 0;

        // for (var i = 0; i < submissions.length; i++) {
        //     var submission = submissions[i];

        //     if (submission.state === "new") {
        //         var creationDate = new Date(submission.creation_date);
        //         var archivedDate = submission.archived_date ? new Date(submission.archived_date) : null;
        //         var deletedDate = submission.deleted_date ? new Date(submission.deleted_date) : null;

        //         if (archivedDate || deletedDate) {
        //             var diffInMilliseconds = (archivedDate || deletedDate).getTime() - creationDate.getTime();
        //             totalDiffInMilliseconds += diffInMilliseconds;
        //             numClosedSubmissions++;
        //         }
        //     }
        // }

        // var averageDiffInMilliseconds = totalDiffInMilliseconds / numClosedSubmissions;
        // var averageDiffInDays = averageDiffInMilliseconds / (1000 * 60 * 60 * 24);
        // $scope.averageDiffInDays = averageDiffInDays.toFixed(2);
        var statusCount = {};

        for (var i = 0; i < $scope.resources.rtips.rtips.length; i++) {
            var status = $scope.resources.rtips.rtips[i].submissionStatusStr;

            if (statusCount[status]) {
                statusCount[status]++;
            } else {
                statusCount[status] = 1;
            }
        }

        var totalItems = $scope.resources.rtips.rtips.length;
        $scope.statusPercentages = [];

        for (var status in statusCount) {
            var count = statusCount[status];
            var percentage = (count / totalItems) * 100;
            $scope.statusPercentages.push({
                status: status,
                count: count,
                percentage: percentage.toFixed(2)
            });
        }
// ======================= Statuses LineGraph ===============================
// var labels = Object.keys($scope.reportCount);
// var data = Object.values($scope.reportCount);

// // Create the chart
// var ctx = document.getElementById('statusLineGraph').getContext('2d');
// var statusLineGraph = new Chart(ctx, {
//     type: 'line',
//     data: {
//         labels: labels,
//         datasets: [{
//             label: 'Reports',
//             data: data,
//             fill: false,
//             borderColor: 'rgb(75, 192, 192)',
//             tension: 0.1
//         }]
//     },
//     options: {
//         responsive: true,
//         scales: {
//             x: {
//                 display: true,
//                 title: {
//                     display: true,
//                     text: 'Month'
//                 }
//             },
//             y: {
//                 display: true,
//                 title: {
//                     display: true,
//                     text: 'Reports'
//                 }
//             }
//         }
//     }
// });
// ==========================================================================
        var reports = $scope.resources.rtips.rtips;
        var reportCountPerMonth = {};

        reports.forEach(function (report) {
            var creationDate = new Date(report.creation_date);
            var month = creationDate.toLocaleString('default', { month: 'long' });
            var year = creationDate.getFullYear();

            var monthYear = month + ' ' + year;
            if (reportCountPerMonth.hasOwnProperty(monthYear)) {
                reportCountPerMonth[monthYear]++;
            } else {
                reportCountPerMonth[monthYear] = 1;
            }
        });
        $scope.reportCount = reportCountPerMonth;
        
        // ===================================== line graph 
        // var jsonData = $scope.resources.rtips.rtips;

        // // Extract the necessary data for the chart
        // var chartData = jsonData.map(function (item) {
        //     return {
        //         year: new Date(item.creation_date).getFullYear(),
        //         month: new Date(item.creation_date).getMonth() + 1,
        //         reports: 1
        //     };
        // });

        // // Group the data by year and month
        // var groupedData = {};
        // console.log(chartData, "chartData");
        // chartData.forEach(function (item) {
        //     var key = item.year + '-' + item.month;
        //     if (groupedData.hasOwnProperty(key)) {
        //         groupedData[key]++;
        //     } else {
        //         groupedData[key] = 1;
        //     }
        // });
        // console.log(groupedData, "groupedData");
        // Extract the labels and data for the chart
        var labels = Object.keys($scope.reportCount);
        var data = Object.values($scope.reportCount);

        // Create the chart
        var ctx = document.getElementById('perMonthLineGraph').getContext('2d');
        var perMonthLineGraph = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Reports',
                    data: data,
                    fill: false,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Month'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Reports'
                        }
                    }
                }
            }
        });
        // =====================================================
        var chartConfig = {
            type: 'doughnut',
            data: {
                labels: [], // Array of status labels
                datasets: [
                    {
                        data: [], // Array of status counts
                        backgroundColor: [] // Array of background colors for each status
                    }
                ]
            },
            options: {
                responsive: true
            },
            
        };

        // Populate chartConfig with your data
        // Example data:
        chartConfig.data.labels = $scope.statusPercentages.map(function (percentage) {
            return percentage.status;
        });

        chartConfig.data.datasets[0].data = $scope.statusPercentages.map(function (percentage) {
            return percentage.count;
        });
        function generateRandomColors(numColors) {
            var colors = [];
            for (var i = 0; i < numColors; i++) {
              var r = Math.floor(Math.random() * 256);
              var g = Math.floor(Math.random() * 256);
              var b = Math.floor(Math.random() * 256);
              colors.push('rgb(' + r + ', ' + g + ', ' + b + ')');
            }
            return colors;
          }
          chartConfig.data.datasets[0].backgroundColor = generateRandomColors(chartConfig.data.datasets[0].data.length);

        // Create the chart
        var ctx = document.getElementById('doughnut').getContext('2d');
        new Chart(ctx, chartConfig);

    }

]);