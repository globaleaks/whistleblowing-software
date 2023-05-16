GL.controller("FeaturesCtrl",
  ["$scope", "$location", "$filter", "$http", "$interval", "$routeParams", "$uibModal", "Authentication", "RTip", "WBTip", "RTipExport", "RTipDownloadRFile", "WBTipDownloadFile", "fieldUtilities", "RTipViewRFile",
    function ($scope, $location, $filter, $http, $interval, $routeParams, $uibModal, Authentication, RTip, WBTip, RTipExport, RTipDownloadRFile, WBTipDownloadFile, fieldUtilities, RTipViewRFile) {

      angular.forEach($scope.resources.rtips.rtips, function (tip) {
        tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText(tip.status, tip.substatus, $scope.submission_statuses);
      });

      $scope.reports = $scope.resources.rtips.rtips;
      $scope.totalReports = $scope.resources.rtips.rtips.length;


      $scope.tipArray = $scope.resources.rtips.rtips;

      // Lable variables
      $scope.labelCounts = {};
      $scope.unlabeledCount = 0;

      // Average Diff In Days  variables
      var totalDiffInMilliseconds = 0;

      // Statuses variables
      var statusCount = {};
      $scope.statusPercentages = [];
      $scope.statues = []

      // Report Count Per Month variables
      var reportCountPerMonth = {};

      // Tor and Http Count variables
      var torCount = 0;
      var httpsCount = 0;

      // UnansweredTips variables
      $scope.unansweredTipsCount = 0;
      // ================================================================
      // TipArray loop
      // ================================================================

      angular.forEach($scope.tipArray, function (tip) {

        // For Lable 
        var label = tip.label;
        if (label) {
          if ($scope.labelCounts[label]) {
            $scope.labelCounts[label]++;
          } else {
            $scope.labelCounts[label] = 1;
          }
        } else {
          $scope.unlabeledCount++;
        }

        // For Average Diff In Days 
        var expirationDate = new Date(tip.expiration_date);
        var updateDate = new Date(tip.update_date);
        var creationDate = new Date(tip.creation_date);
        var updateDiffInMilliseconds = updateDate.getTime() - creationDate.getTime();
        var expirationDiffInMilliseconds = expirationDate.getTime() - creationDate.getTime();
        totalDiffInMilliseconds += (updateDiffInMilliseconds + expirationDiffInMilliseconds);

        // For Statuses
        var status = tip.submissionStatusStr;
        if (statusCount[status]) {
          statusCount[status]++;
        } else {
          statusCount[status] = 1;
        }

        //For Report Count Per Month
        var creationDate = new Date(tip.creation_date);
        var month = creationDate.toLocaleString('default', { month: 'long' });
        var year = creationDate.getFullYear();
        var monthYear = month + ' ' + year;
        if (reportCountPerMonth.hasOwnProperty(monthYear)) {
          reportCountPerMonth[monthYear]++;
        } else {
          reportCountPerMonth[monthYear] = 1;
        }

        //For Tor and Http Count
        if (tip.tor === true) {
          torCount++;
        }
        else {
          httpsCount++;
        }

        //For UnansweredTips Count
        if (tip.submissionstatusestr === 'new') {
          $scope.unansweredTipsCount++;
        }

      })



      // ======================= Lables Stat ===============================

      var totalItemCount = $scope.totalReports;

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


      var labelCountsData = Object.values($scope.labelCounts).map(function (label) {
        return label.count;
      });

      var unlabeledCountData = $scope.unlabeledCount.count;
      var totalReports = $scope.totalReports
      console.log(unlabeledCountData, totalReports);
      var labelCountsCtx = document.getElementById('labelCountsChart').getContext('2d');
      new Chart(labelCountsCtx, {
        type: 'bar',
        data: {
          labels: ['Total Reports', ...Object.keys($scope.labelCounts), 'Unlabeled'],
          datasets: [{
            label: 'Label Counts',
            data: [totalReports, ...labelCountsData, unlabeledCountData],
            backgroundColor: generateRandomColors(Object.keys($scope.labelCounts).length + 2)
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          scales: {
            x: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Number of Reports'
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Label'
              }
            }
          }
        }
      });

      // =========================== AverageDiffInDays Stat  ===============================================

      var averageDiffInMilliseconds = totalDiffInMilliseconds / (2 * $scope.totalReports);
      var averageDiffInDay = averageDiffInMilliseconds / (1000 * 60 * 60 * 24);
      $scope.averageDiffInDays = averageDiffInDay.toFixed(2);

      // =========================== Average DiffInDays of Deleted or Achived Reports stat  ===============================================

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



      // =========================== Statuses Stat  ===============================================
      for (var status in statusCount) {
        var count = statusCount[status];
        var percentage = (count / $scope.totalReports) * 100;
        $scope.statusPercentages.push({
          status: status,
          count: count,
          percentage: percentage.toFixed(2)
        });
        $scope.statues.push({
          status: status,
          count: count,
          percentage: percentage.toFixed(2)
        });
      }
      $scope.statusPercentages.sort((a, b) => {
        const statusA = a.status.toLowerCase();
        const statusB = b.status.toLowerCase();
        if (statusA < statusB) return -1;
        if (statusA > statusB) return 1;
        return 0;
      });

      $scope.statusPercentages.unshift({
        status: 'Total Reports',
        count: $scope.totalReports,
        percentage: 100
      });

      // ======================= Statuses LineGraph ===============================
      var statusLabels = $scope.statusPercentages.map(function (item) {
        return item.status;
      });

      var statusData = $scope.statusPercentages.map(function (item) {
        return item.count;
      });

      // Create the chart
      var statusCtx = document.getElementById('statusBarChart').getContext('2d');
      var statusBarChart = new Chart(statusCtx, {
        type: 'bar',
        data: {
          labels: statusLabels,
          datasets: [{
            label: 'Statuses',
            data: statusData,
            backgroundColor: generateRandomColors(statusData.length)
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          scales: {
            x: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Number of Reports'
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Status'
              }
            }
          }
        }
      });
      // ================================== Statuses Doughnut ===============================
      var chartConfig = {
        type: 'doughnut',
        data: {
          labels: [],
          datasets: [
            {
              data: [],
              backgroundColor: []
            }
          ]
        },
        options: {
          responsive: true,
          // plugins: {
          //   datalabels: {
          //     color: '#fff',
          //     font: {
          //       weight: 'bold',
          //       size: 14
          //     },
          //     formatter: function(value, context) {
          //       if (context.chart.data.labels.indexOf(context.dataset.label) === 0) {
          //         return 'Total: ' + value;
          //       } else {
          //         return value;
          //       }
          //     }
          //   }
          // }
        }
      };
      chartConfig.data.labels = $scope.statues.map(function (percentage) {
        return percentage.status;
      });

      chartConfig.data.datasets[0].data = $scope.statues.map(function (percentage) {
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
      var ctx = document.getElementById('doughnut').getContext('2d');
      new Chart(ctx, chartConfig);

      // ============================ Report Count Per Month stat ==============================================
      $scope.reportCount = reportCountPerMonth;

      // ===================================== Report Count Per Month line graph ==================================
      var labels = Object.keys($scope.reportCount);
      var data = Object.values($scope.reportCount);
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

      // ============================== Tor and Https connection stat ==============================================

      $scope.torPercentage = (torCount / $scope.resources.rtips.rtips.length) * 100;
      $scope.httpsPercentage = (httpsCount / $scope.resources.rtips.rtips.length) * 100;
      $scope.torCount = torCount;
      $scope.httpsCount = httpsCount;

      // ============================== Average response time for whistleblower/receiver Stat =============================================

      var whistleblowerTotalTime = 0;
      var whistleblowerCount = 0;
      var recipientTotalTime = 0;
      var recipientCount = 0;

      angular.forEach($scope.resources.rtips.rtips, function (tip) {
        $scope.tip = new RTip({ id: tip.id }, function (tip) {
          $scope.tip = tip;
          $scope.tip.context = $scope.contexts_by_id[$scope.tip.context_id];

          angular.forEach($scope.tip.comments, function (comment) {
            var responseTime = new Date() - new Date(comment.creation_date);
            if (comment.type === 'whistleblower') {
              whistleblowerTotalTime += responseTime;
              whistleblowerCount++;
            } else if (comment.type === 'receiver') {
              recipientTotalTime += responseTime;
              recipientCount++;
            }
          });
        });
      });
      var whistleblowerAverageTime = whistleblowerTotalTime / whistleblowerCount;
      var recipientAverageTime = recipientTotalTime / recipientCount;
      console.log(whistleblowerAverageTime, recipientAverageTime);

      console.log('Average response time for whistleblower comments: ' + whistleblowerAverageTime + ' milliseconds');
      console.log('Average response time for recipient comments: ' + recipientAverageTime + ' milliseconds');

      // =========================================== UnansweredTips Stat ======================================        
      console.log($scope.unansweredTipsCount, "unansweredTipsCount");

      // =========================================== Chart plugin register ======================================        
      // chart plugin register
      // Chart.register(ChartDataLabels);

    }

  ]);
