GL.controller("ReceiverTipsCtrl", ["$scope", "$filter", "$http", "$location", "$uibModal", "$window", "RTipExport", "TokenResource",
  function ($scope, $filter, $http, $location, $uibModal, $window, RTipExport, TokenResource) {

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

    var unique_keys = [];
    angular.forEach($scope.resources.rtips.rtips, function (tip) {
      tip.context = $scope.contexts_by_id[tip.context_id];
      tip.context_name = tip.context.name;
      tip.questionnaire = $scope.resources.rtips.questionnaires[tip.questionnaire];
      tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText(tip.status, tip.substatus, $scope.submission_statuses);
      //  alert(JSON.stringify(tip))
      console.log($scope.resources.rtips, "$scope.resources.rtips");

      if (unique_keys.includes(tip.submissionStatusStr) === false) {
        unique_keys.push(tip.submissionStatusStr);
        $scope.dropdownStatusData.push({ id: $scope.dropdownStatusData.length + 1, label: tip.submissionStatusStr });
      }

      if (unique_keys.includes(tip.context_name) === false) {
        unique_keys.push(tip.context_name);
        $scope.dropdownContextData.push({ id: $scope.dropdownContextData.length + 1, label: tip.context_name });
      }

      var scoreLabel = $scope.Utils.maskScore(tip.score);

      if (unique_keys.includes(scoreLabel) === false) {
        unique_keys.push(scoreLabel);
        $scope.dropdownScoreData.push({ id: $scope.dropdownScoreData.length + 1, label: scoreLabel });
      }
    });

    $scope.filteredTips = $filter("orderBy")($scope.resources.rtips.rtips, "update_date");

    $scope.dropdownDefaultText = {
      buttonDefaultText: "",
      searchPlaceholder: $filter("translate")("Search")
    };

    function applyFilter() {
      $scope.filteredTips = $scope.Utils.getStaticFilter($scope.resources.rtips.rtips, $scope.dropdownStatusModel, "submissionStatusStr");
      $scope.filteredTips = $scope.Utils.getStaticFilter($scope.filteredTips, $scope.dropdownContextModel, "context_name");
      $scope.filteredTips = $scope.Utils.getStaticFilter($scope.filteredTips, $scope.dropdownScoreModel, "score");
      $scope.filteredTips = $scope.Utils.getDateFilter($scope.filteredTips, $scope.reportDateFilter, $scope.updateDateFilter, $scope.expiryDateFilter);
    }

    $scope.on_changed = {
      onSelectionChanged: function () {
        applyFilter();
      }
    };

    $scope.onReportFilterChange = function (reportFilter) {
      $scope.reportDateFilter = reportFilter;
      applyFilter();
    };

    $scope.onUpdateFilterChange = function (updateFilter) {
      $scope.updateDateFilter = updateFilter;
      applyFilter();
    };

    $scope.onExpiryFilterChange = function (expiryFilter) {
      $scope.expiryDateFilter = expiryFilter;
      applyFilter();
    };

    $scope.checkFilter = function (filter) {
      return filter.length > 0;
    };

    $scope.$watch("search", function (value) {
      if (typeof value !== "undefined") {
        $scope.currentPage = 1;
        $scope.filteredTips = $filter("orderBy")($filter("filter")($scope.resources.rtips.rtips, value), "update_date");
      }
    });

    $scope.open_grant_access_modal = function () {
      return $scope.Utils.runUserOperation("get_users_names").then(function (response) {
        $uibModal.open({
          templateUrl: "views/modals/grant_access.html",
          controller: "ConfirmableModalCtrl",
          resolve: {
            arg: {
              users_names: response.data
            },
            confirmFun: function () {
              return function (receiver_id) {
                var args = {
                  rtips: $scope.selected_tips,
                  receiver: receiver_id
                };

                return $scope.Utils.runRecipientOperation("grant", args, true);
              };
            },
            cancelFun: null
          }
        });
      });
    };

    $scope.open_revoke_access_modal = function () {
      return $scope.Utils.runUserOperation("get_user_names").then(function (response) {
        $uibModal.open({
          templateUrl: "views/modals/revoke_access.html",
          controller: "ConfirmableModalCtrl",
          resolve: {
            arg: {
              users_names: response.data
            },
            confirmFun: function () {
              return function (receiver_id) {
                var args = {
                  rtips: $scope.selected_tips,
                  receiver: receiver_id
                };

                return $scope.Utils.runRecipientOperation("revoke", args, true);
              };
            },
            cancelFun: null
          }
        });
      });
    };

    $scope.exportTip = RTipExport;

    $scope.selected_tips = [];

    $scope.select_all = function () {
      $scope.selected_tips = [];
      angular.forEach($scope.filteredTips, function (tip) {
        $scope.selected_tips.push(tip.id);
      });
    };

    $scope.toggle_star = function (tip) {
      return $http({
        method: "PUT",
        url: "api/rtips/" + tip.id,
        data: {
          "operation": "set",
          "args": {
            "key": "important",
            "value": !tip.important
          }
        }
      }).then(function () {
        tip.important = !tip.important;
      });
    };

    $scope.deselect_all = function () {
      $scope.selected_tips = [];
    };

    $scope.tip_switch = function (id) {
      var index = $scope.selected_tips.indexOf(id);
      if (index > -1) {
        $scope.selected_tips.splice(index, 1);
      } else {
        $scope.selected_tips.push(id);
      }
    };

    $scope.isSelected = function (id) {
      return $scope.selected_tips.indexOf(id) !== -1;
    };

    $scope.markReportStatus = function (date) {
      var report_date = new Date(date);
      var current_date = new Date();
      return current_date > report_date;
    };

    $scope.tip_delete_selected = function () {
      $uibModal.open({
        templateUrl: "views/modals/delete_confirmation.html",
        controller: "TipBulkOperationsCtrl",
        resolve: {
          selected_tips: function () {
            return $scope.selected_tips;
          },
          operation: function () {
            return "delete";
          }
        }
      });
    };

    $scope.tips_export = function () {
      for (var i = 0; i < $scope.selected_tips.length; i++) {
        (function (i) {
          new TokenResource().$get().then(function (token) {
            return $window.open("api/rtips/" + $scope.selected_tips[i] + "/export?token=" + token.id + ":" + token.answer);
          });
        })(i);
      }
    };
  }])
  .controller("TipBulkOperationsCtrl", ["$scope", "$http", "$location", "$uibModalInstance", "selected_tips", "operation",
    function ($scope, $http, $location, $uibModalInstance, selected_tips, operation) {
      $scope.selected_tips = selected_tips;
      $scope.operation = operation;

      $scope.cancel = function () {
        $uibModalInstance.close();
      };

      $scope.confirm = function () {
        $uibModalInstance.close();

        if (["delete"].indexOf(operation) === -1) {
          return;
        }

        return $scope.Utils.runRecipientOperation($scope.operation, { "rtips": $scope.selected_tips }, true);
      };

    }])
  .controller("StatisticsCtrl", ["$scope", "$location", "$filter", "$http", "$interval", "$routeParams", "$uibModal", "Authentication", "RTip", "WBTip", "RTipExport", "RTipDownloadRFile", "WBTipDownloadFile", "fieldUtilities", "RTipViewRFile",
    function ($scope, $location, $filter, $http, $interval, $routeParams, $uibModal, Authentication, RTip, WBTip, RTipExport, RTipDownloadRFile, WBTipDownloadFile, fieldUtilities, RTipViewRFile) {


      angular.forEach($scope.resources.rtips.rtips, function (tip) {
        tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText(tip.status, tip.substatus, $scope.submission_statuses);
      });
      $scope.reportingChannel = []
      $scope.reports = $scope.resources.rtips.rtips;
      $scope.totalReports = $scope.resources.rtips.rtips.length;
      console.log($scope.reports);

      $scope.tipArray = $scope.resources.rtips.rtips;

      // Lable variables
      $scope.labelCounts = {};
      $scope.unlabeledCount = 0;
      $scope.unlabeledCountDefault = 0;
      $scope.labeledCountDefault = 0;

      // Average Diff In Days  variables
      var totalDiffInMilliseconds = 0;

      // Statuses variables
      $scope.statusCount = {};
      $scope.statusCount['New'] = 0
      $scope.statusCount['Opened'] = 0
      $scope.statusCount['Closed'] = 0
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
          $scope.labeledCountDefault++;
        } else {
          $scope.unlabeledCount++;
          $scope.unlabeledCountDefault++;
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
        if ($scope.statusCount[status]) {
          $scope.statusCount[status]++;
        } else {
          $scope.statusCount[status] = 1;
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

      //  var submissions = $scope.resources.rtips.rtips;
      //  var totalDiffInMilliseconds = 0;
      //  var numClosedSubmissions = 0;

      //  for (var i = 0; i < submissions.length; i++) {
      //      var submission = submissions[i];

      //      if (submission.state === "new") {
      //          var creationDate = new Date(submission.creation_date);
      //          var archivedDate = submission.archived_date ? new Date(submission.archived_date) : null;
      //          var deletedDate = submission.deleted_date ? new Date(submission.deleted_date) : null;

      //          if (archivedDate || deletedDate) {
      //              var diffInMilliseconds = (archivedDate || deletedDate).getTime() - creationDate.getTime();
      //              totalDiffInMilliseconds += diffInMilliseconds;
      //              numClosedSubmissions++;
      //          }
      //      }
      //  }

      //  var averageDiffInMilliseconds = totalDiffInMilliseconds / numClosedSubmissions;
      //  var averageDiffInDays = averageDiffInMilliseconds / (1000 * 60 * 60 * 24);
      //  $scope.averageDiffInDays = averageDiffInDays.toFixed(2);



      // =========================== Statuses Stat  ===============================================
      for (var status in $scope.statusCount) {
        var count = $scope.statusCount[status];
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
      $scope.statuses =function(){}
      var statusLabels = $scope.statusPercentages.map(function (item) {
        return item.status + "  |  " + item.percentage + " %";
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
            backgroundColor: 'rgba(55, 122, 188, 0.6)',
            // barThickness: 60,
            // maxBarThickness: 60,
            label: 'Statuses',
            data: statusData,
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
        },
       
      });
      // ================================== Statuses Doughnut ===============================
      // var chartConfig = {
      //   type: 'doughnut',
      //   data: {
      //     labels: [],
      //     datasets: [
      //       {
      //         data: [],
      //         backgroundColor: []
      //       }
      //     ]
      //   },
      //   options: {
      //     responsive: true,
      //     plugins: {
      //       datalabels: {
      //         color: '#fff',
      //         font: {
      //           weight: 'bold',
      //           size: 14
      //         },
      //         formatter: function (value, context) {
      //           if (context.chart.data.labels.indexOf(context.dataset.label) === 0) {
      //             return 'Total: ' + value;
      //           } else {
      //             return value;
      //           }
      //         }
      //       }
      //     }
      //   }
      // };
      // chartConfig.data.labels = $scope.statues.map(function (percentage) {
      //   return percentage.status;
      // });

      // chartConfig.data.datasets[0].data = $scope.statues.map(function (percentage) {
      //   return percentage.count;
      // });
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
      // chartConfig.data.datasets[0].backgroundColor = generateRandomColors(chartConfig.data.datasets[0].data.length);
      // var ctx = document.getElementById('doughnut').getContext('2d');
      // new Chart(ctx, chartConfig);

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
      $scope.channel = 'Default';

      $scope.startDate = null;
      $scope.endDate = null;
      $scope.startDatePickerOpen = false;
      $scope.endDatePickerOpen = false;
      $scope.format = 'dd/MM/yyyy';

      $scope.openStartDatePicker = function () {
        $scope.startDatePickerOpen = true;
      };

      $scope.openEndDatePicker = function () {
        $scope.endDatePickerOpen = true;
      };


      // function filterData() {
      //   var startDate = new Date(document.getElementById("startDate").value);
      //   var endDate = new Date(document.getElementById("endDate").value);
      //   console.log(endDate, "endDate", startDate, "startDate");
      //   var filteredData = $scope.reports.filter(function (obj) {
      //     var creationDate = new Date(obj.creation_date);
      //     // return obj.chancel === chancel && creationDate >= startDate && creationDate <= endDate;
      //     return creationDate >= startDate && creationDate <= endDate;
      //   });

      //   console.log(filteredData);
      // }

      // document.getElementById("startDate").addEventListener("change", filterData);
      // document.getElementById("endDate").addEventListener("change", filterData);

      //=============================== Filter Function ==================================

      // $scope.filterData = function() {
      //   var startDate = new Date($scope.startDate);
      //   var endDate = new Date($scope.endDate);
      //   console.log(endDate, "endDate", startDate, "startDate");

      //   var filteredData = $scope.reports.filter(function(obj) {
      //     var creationDate = new Date(obj.creation_date);
      //     return creationDate >= startDate && creationDate <= endDate;
      //   });

      //   console.log(filteredData);
      // };

      // $scope.$watchGroup(['startDate', 'endDate'], function() {
      //   $scope.filterData();
      // });

      // ========================================================================

      totalReports


      // var startDate = new Date('2023-05-01');
      // var endDate = new Date('2023-05-31');
      // var chancel = "some chancel value";

      // var filteredData = $scope.reports.filter(function (obj) {
      //   var creationDate = new Date(obj.creation_date);
      //   return obj.chancel === chancel && creationDate >= startDate && creationDate <= endDate;
      // });

      // ============================== Average response time for whistleblower/receiver Stat =============================================

      var whistleblowerTotalTime = 0;
      var whistleblowerCount = 0;
      var recipientTotalTime = 0;
      var recipientCount = 0;

      angular.forEach($scope.resources.rtips.rtips, function (tip) {
        $scope.tip = new RTip({ id: tip.id }, function (tip) {
          $scope.tip = tip;
          $scope.tip.context = $scope.contexts_by_id[$scope.tip.context_id];

          var valueToAdd = $scope.tip.context.name;
          if ($scope.reportingChannel.indexOf(valueToAdd) === -1) {
            $scope.reportingChannel.push(valueToAdd);
            // alert(valueToAdd);
          }

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
      //   chart plugin register
      //   Chart.register(ChartDataLabels);
      $scope.filteredData = $scope.tipArray
      $scope.filterData = function () {
        var startDate = new Date($scope.startDate);
        var endDate = new Date($scope.endDate);
        console.log(endDate, "endDate", startDate, "startDate");

        $scope.filteredData = $scope.tipArray.filter(function (obj) {
          var creationDate = new Date(obj.creation_date);
          return creationDate >= startDate && creationDate <= endDate;
        });
      };

      $scope.$watchGroup(['startDate', 'endDate'], function () {
        $scope.filterData();
      });
    }]);
