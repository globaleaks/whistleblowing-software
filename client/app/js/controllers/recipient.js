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

      function generateBarGraph(documentID, context, type, graphLabels, graphTitle, graphData, xlabel, ylabel, update) {

        var canvas = document.getElementById(documentID);
        var ctx = document.getElementById(documentID).getContext(context);
        var chart = new Chart(ctx, {
          type: type,
          data: {
            labels: graphLabels,
            datasets: [{
              backgroundColor: 'rgba(55, 122, 188, 0.6)',
              label: graphTitle,
              data: graphData,
            }]
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            barPercentage: 0.6,
            categoryPercentage: 0.6,

            scales: {
              x: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: xlabel
                }
              },
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: ylabel
                }
              }
            }
          },
        });
        return chart;
      }
      function generateLineGraph(documentID, context, type, graphLabels, graphTitle, graphData, xlabel, ylabel) {
        var ctx = document.getElementById(documentID).getContext(context);
        var graph = new Chart(ctx, {
          type: type,
          data: {
            labels: graphLabels,
            datasets: [{
              label: graphTitle,
              data: graphData,
              fill: false,
              borderColor: 'rgb(75, 192, 192)',
              tension: 0.1
            }]
          },
          options: {
            // indexAxis: 'y',
            responsive: true,
            scales: {
              x: {
                display: true,
                title: {
                  display: true,
                  text: xlabel
                }
              },
              y: {
                display: true,
                title: {
                  display: true,
                  text: ylabel
                }
              }
            }
          },
        });
        return graph;
      }

      $scope.channel = undefined
      $scope.startDate = null;
      $scope.endDate = null;

      var totalClosureTime = 0;
      var reportCountPerMonth = {};
      var httpsCount = 0;
      var statusBarChart = undefined;
      var labelCountsChart = undefined;
      var perMonthLineGraph = undefined;
      var channelCountsChart =undefined;
      var totalClosedTips = 0;

      $scope.flush = function () {
        $scope.reports = $scope.resources.rtips.rtips;
        $scope.totalReports = 0;
        $scope.reportingChannel = []
        $scope.statusCount = { 'New': 0, 'Opened': 0, 'Closed': 0 };
        $scope.statusPercentages = [];
        $scope.statues = []
        $scope.unansweredTipsCount = 0;
        $scope.receiverCount = 0;
        $scope.startDatePickerOpen = false;
        $scope.endDatePickerOpen = false;
        $scope.format = 'dd/MM/yyyy';
        $scope.unansweredTips = [];
        $scope.unansweredCount = 0;
        $scope.labelCounts = {};
        $scope.unlabeledCount = 0;
        $scope.unlabeledCountDefault = 0;
        $scope.labeledCountDefault = 0;
        $scope.torCount = 0;
        $scope.reciprocatingWhistleBlower = 0;
        $scope.channelsArray = []
        $scope.averageClosureTime = 0;

        totalClosedTips = 0
        totalClosureTime = 0;
        reportCountPerMonth = {};
        httpsCount = 0;
      }
      console.log("$scope.resources.rtips.rtips",$scope.resources.rtips.rtips);

      $scope.flush()
      $scope.initializeTips = function () {
        for (var tip of $scope.resources.rtips.rtips) {
          tip.context = $scope.contexts_by_id[tip.context_id];
          tip.context_name = tip.context.name;
          var valueToAdd = tip.context.name;
          if ($scope.reportingChannel.indexOf(valueToAdd) === -1) {
            $scope.reportingChannel.push(valueToAdd);
          }

          var creationDate = new Date(tip.creation_date);
          var expirationDate = new Date(tip.expiration_date);
          if ($scope.channel && tip.context_name != $scope.channel || $scope.startDate && $scope.startDate > creationDate || $scope.endDate && $scope.endDate < expirationDate) {
            continue
          }

          $scope.totalReports += 1
          tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText(tip.status, tip.substatus, $scope.submission_statuses);
          if (tip.submissionstatusestr === 'New') {
            $scope.tip = new RTip({ id: tip.id }, function (tip) {

              for (var item of tip.comments) {

                if (item.type === "receiver") {
                  $scope.receiverCount++
                }
              }

              for (var item of tip.comments) {
                unanswered = true
                if (item.type === 'whistleblower') {
                  for (var receiver of tip.comments) {
                    if (receiver.type === 'receiver') {
                      unanswered = false
                      break;
                    }
                  }
                  if (unanswered) {
                    $scope.unansweredTips.push(item);
                    $scope.unansweredCount++;
                  }
                  break
                }
              }
            })
          }

          var expirationDate = new Date(tip.expiration_date);
          var updateDate = new Date(tip.update_date);
          var creationDate = new Date(tip.creation_date);
          var lastAccessDate = new Date(tip.last_access);
          var updateDiffInMilliseconds = updateDate.getTime() - creationDate.getTime();
          var expirationDiffInMilliseconds = expirationDate.getTime() - creationDate.getTime();

          /* For Statuses */
          var status = tip.submissionStatusStr;
          if ($scope.statusCount[status]) {
            $scope.statusCount[status]++;
          } else {
            $scope.statusCount[status] = 1;
          }

          /* For Report Count Per Month */
          var creationDate = new Date(tip.creation_date);
          var month = creationDate.toLocaleString('default', { month: 'long' });
          var year = creationDate.getFullYear();
          var monthYear = month + ' ' + year;
          if (reportCountPerMonth.hasOwnProperty(monthYear)) {
            reportCountPerMonth[monthYear]++;
          } else {
            reportCountPerMonth[monthYear] = 1;
          }

          /* For Tor and Http Count */

          //last_access

          creationDate.setSeconds(0);
          lastAccessDate.setSeconds(0);
          if(lastAccessDate.getTime()!=creationDate.getTime()){
              $scope.reciprocatingWhistleBlower++;
          }

          if (tip.tor === true) {
            torCount++;
          }
          else {
            httpsCount++;
          }

          /* For UnansweredTips Count */
          if (tip.submissionstatusestr === 'new') {
            $scope.unansweredTipsCount++;
          }

          //  For The average time of closure of the submission
          var report = tip;
          var reportCreationDate = new Date(report.creation_date);
          var reportUpdateDate = new Date(report.update_date);
          var closureTime = reportUpdateDate.getTime() - reportCreationDate.getTime();
          if(status=="Closed"){
              $scope.averageClosureTime += closureTime;
              totalClosedTips+=1
          }

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

          // For ChannelS
          $scope.channelsArray.push({ Channel: tip.context.name })

        }
      }
      /* =============================================== General Statistics =============================================== */

      $scope.generateGeneralGraph = function () {
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

        var statusLabels = $scope.statusPercentages.map(function (item) {
          return item.status + " | " + item.percentage + " %";
        });
        var statusData = $scope.statusPercentages.map(function (item) {
          return item.count;
        });

        if (statusBarChart) {
          statusBarChart.data.labels = statusLabels;
          statusBarChart.data.datasets[0].data = statusData;
          statusBarChart.update();
        } else {
          statusBarChart = generateBarGraph('statusBarChart', '2d', 'bar', statusLabels, 'General Statistics', statusData, 'Number of Reports', 'Status')
        }
      };

      /* =============================================== Date Statistics =============================================== */

      $scope.openStartDatePicker = function () {
        $scope.startDatePickerOpen = true;
      };

      $scope.openEndDatePicker = function () {
        $scope.endDatePickerOpen = true;
      };

      /* =============================================== Interaction Statistics =============================================== */

      $scope.generateInteractionLineGraph = function () {
        $scope.averageClosureTime = (($scope.averageClosureTime / totalClosedTips) / (1000 * 60 * 60 * 24)).toFixed(3);
        if($scope.averageClosureTime == 0){
            $scope.averageClosureTime = 0
        }

        var reportCount = reportCountPerMonth;
        var labels = Object.keys(reportCount);
        var reportData = Object.values(reportCount);


        if (perMonthLineGraph) {
          perMonthLineGraph.data.labels = labels;
          perMonthLineGraph.data.datasets[0].data = reportData;
          perMonthLineGraph.update();
        } else {
          perMonthLineGraph = generateLineGraph('perMonthLineGraph', '2d', 'line', labels, 'Interaction Stataistics', reportData, 'Month', 'Reports')
        }

      }

      /* =============================================== Label Statistics =============================================== */

      $scope.generateLabelGraph = function () {

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
        var labels = ['Total Reports', ...Object.keys($scope.labelCounts), 'Unlabeled']
        var data = [totalReports, ...labelCountsData, unlabeledCountData]


        if (labelCountsChart) {
          labelCountsChart.data.labels = labels;
          labelCountsChart.data.datasets[0].data = data;
          labelCountsChart.update();
        } else {
          labelCountsChart = generateBarGraph('labelCountsChart', '2d', 'bar', labels, 'Labels Stataistics', data, 'Number of Reports', 'Label')
        }

      }

      /* =============================================== Channels Statistics =============================================== */

      $scope.generateChannelGraph = function () {

        $scope.groupChannels = function (channels) {
          var groupedChannels = {};

          channels.forEach(function (channel) {
            if (groupedChannels[channel.Channel]) {
              groupedChannels[channel.Channel].push(channel);
            } else {
              groupedChannels[channel.Channel] = [channel];
            }
          });

          return groupedChannels;
        };

        var groupedChannels = $scope.groupChannels($scope.channelsArray);

        var ChannelLabels = [];
        var ChannelData = [];

        for (var channel in groupedChannels) {
          ChannelLabels.push(channel);
          ChannelData.push(groupedChannels[channel].length);
        }
        $scope.chartLabels = ChannelLabels;
        $scope.chartData = ChannelData;
        var totalReports = $scope.totalReports

        var labels = ['Total Reports', ...$scope.chartLabels]
        var data = [totalReports, ...$scope.chartData]
        if (channelCountsChart) {
          channelCountsChart.data.labels = labels;
          channelCountsChart.data.datasets[0].data = data;
          channelCountsChart.update();
        } else {
          channelCountsChart = generateBarGraph('reportingChannelChart', '2d', 'bar', labels, 'Channels Stataistics', data, 'Number of Reports', 'Channels')
        }

      }

      /* =============================================== Filters =============================================== */

      $scope.initialize = function () {
        $scope.flush()

        $scope.initializeTips()
        $scope.generateLabelGraph();
        $scope.generateInteractionLineGraph();
        $scope.generateGeneralGraph();
        $scope.generateChannelGraph();
      }
      $scope.initialize();

     /* =============================================== Helper Methods =============================================== */

     $scope.statPercentageCalculator = function (value, totalvalue) {
       if(!totalvalue){
         return 0;
       }else{
         return (value/totalvalue)*100
       }
     }

}]);

