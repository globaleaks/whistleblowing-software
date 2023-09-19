GL.controller("ReceiverTipsCtrl", ["$scope",  "$filter", "$http", "$location", "$uibModal", "$window", "RTipExport", "TokenResource",
  function($scope, $filter, $http, $location, $uibModal, $window, RTipExport, TokenResource) {

  $scope.search = undefined;
  $scope.currentPage = 1;
  $scope.itemsPerPage = 20;
  $scope.dropdownSettings = {dynamicTitle: false, showCheckAll: false, showUncheckAll: false, enableSearch: true, displayProp: "label", idProp: "label", itemsShowLimit: 5};

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
  angular.forEach($scope.resources.rtips, function(tip) {
     tip.context = $scope.contexts_by_id[tip.context_id];
     tip.context_name = tip.context.name;
     tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText(tip.status, tip.substatus, $scope.submission_statuses);

     if (unique_keys.includes(tip.submissionStatusStr) === false) {
       unique_keys.push(tip.submissionStatusStr);
       $scope.dropdownStatusData.push({id: $scope.dropdownStatusData.length + 1, label: tip.submissionStatusStr});
     }

     if (unique_keys.includes(tip.context_name) === false) {
       unique_keys.push(tip.context_name);
       $scope.dropdownContextData.push({id: $scope.dropdownContextData.length + 1, label: tip.context_name});
     }

     var scoreLabel = $scope.Utils.maskScore(tip.score);

     if (unique_keys.includes(scoreLabel) === false) {
       unique_keys.push(scoreLabel);
       $scope.dropdownScoreData.push({id: $scope.dropdownScoreData.length + 1, label: scoreLabel});
     }
  });

  $scope.filteredTips = $filter("orderBy")($scope.resources.rtips, "update_date");

  $scope.dropdownDefaultText = {
    buttonDefaultText: "",
    searchPlaceholder: $filter("translate")("Search")
  };

  function applyFilter()
  {
     $scope.filteredTips = $scope.Utils.getStaticFilter($scope.resources.rtips, $scope.dropdownStatusModel, "submissionStatusStr");
     $scope.filteredTips = $scope.Utils.getStaticFilter($scope.filteredTips, $scope.dropdownContextModel, "context_name");
     $scope.filteredTips = $scope.Utils.getStaticFilter($scope.filteredTips, $scope.dropdownScoreModel, "score");
     $scope.filteredTips = $scope.Utils.getDateFilter($scope.filteredTips, $scope.reportDateFilter, $scope.updateDateFilter, $scope.expiryDateFilter);
  }

  $scope.on_changed = {
    onSelectionChanged: function() {
      applyFilter();
    }
  };

  $scope.onReportFilterChange = function(reportFilter) {
    $scope.reportDateFilter = reportFilter;
    applyFilter();
  };

  $scope.onUpdateFilterChange = function(updateFilter) {
    $scope.updateDateFilter = updateFilter;
    applyFilter();
  };

  $scope.onExpiryFilterChange = function(expiryFilter) {
    $scope.expiryDateFilter = expiryFilter;
    applyFilter();
  };

  $scope.checkFilter = function(filter) {
    return filter.length > 0;
  };

  $scope.$watch("search", function (value) {
    if (typeof value !== "undefined") {
      $scope.currentPage = 1;
      $scope.filteredTips = $filter("orderBy")($filter("filter")($scope.resources.rtips, value), "update_date");
    }
  });

  $scope.open_grant_access_modal = function () {
    return $scope.Utils.runUserOperation("get_users_names").then(function(response) {
      var selectable_recipients = [];

      $scope.public.receivers.forEach(async (receiver) => {
        if (receiver.id !== $scope.Authentication.session.user_id) {
          selectable_recipients.push(receiver);
        }
      });

      $uibModal.open({
      templateUrl: "views/modals/grant_access.html",
        controller: "ConfirmableModalCtrl",
        resolve: {
          arg: {
            users_names: response.data,
            selectable_recipients: selectable_recipients
          },
          confirmFun: function() {
            return function(receiver_id) {
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
    return $scope.Utils.runUserOperation("get_users_names").then(function(response) {
      var selectable_recipients = [];

      $scope.public.receivers.forEach(async (receiver) => {
        if (receiver.id !== $scope.Authentication.session.user_id) {
          selectable_recipients.push(receiver);
        }
      });

      $uibModal.open({
      templateUrl: "views/modals/revoke_access.html",
        controller: "ConfirmableModalCtrl",
        resolve: {
          arg: {
            users_names: response.data,
            selectable_recipients: selectable_recipients
          },
          confirmFun: function() {
            return function(receiver_id) {
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

  $scope.toggle_star = function(tip) {
    return $http({
      method: "PUT",
      url: "api/recipient/rtips/" + tip.id,
      data: {
        "operation": "set",
        "args": {
          "key": "important",
          "value": !tip.important
        }
      }
    }).then(function() {
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

  $scope.tips_export = function () {
    for(var i=0; i<$scope.selected_tips.length; i++) {
      (function(i) {
        new TokenResource().$get().then(function(token) {
          return $window.open("api/recipient/rtips/" + $scope.selected_tips[i] + "/export?token=" + token.id + ":" + token.answer);
        });
      })(i);
    }
  };
}])
.controller("StatisticsCtrl", ["$scope", "RTip", "Statistics",
  function ($scope, RTip, Statistics) {

     var statsModel = Statistics.getStatisticsModel();

    $scope.flush = function () {
      $scope.reportingChannel = [];
      $scope.startDatePickerOpen = false;
      $scope.endDatePickerOpen = false;
      $scope.staticData = [];

     statsModel = Statistics.getStatisticsModel();
     answerArray = [];
     dropdownOptions = [];

    };

    $scope.openStartDatePicker = function () {
      $scope.startDatePickerOpen = true;
    };

    $scope.openEndDatePicker = function () {
      $scope.endDatePickerOpen = true;
    };

    $scope.initializeTips = function () {
      let promises = [];

      for (let tip of $scope.resources.rtips) {
        tip.context = $scope.contexts_by_id[tip.context_id];

        if ($scope.reportingChannel.indexOf(tip.context.name) === -1) {
          $scope.reportingChannel.push(tip.context.name);
        }

        let creationDate = new Date(tip.creation_date);
        let expirationDate = new Date(tip.expiration_date);

        if (($scope.channel && tip.context.name !== $scope.channel) ||
          ($scope.startDate && $scope.startDate > creationDate) ||
          ($scope.endDate && $scope.endDate < expirationDate)) {
          continue;
        }

        statsModel.totalReports += 1;
        statsModel.reports.push(tip);

        tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText(tip.status, tip.substatus, $scope.submission_statuses);

        if (tip.status !== 'new') {
          let promise = new Promise(function(resolve, reject) {
            RTip({ id: tip.id }, function (tip) {
              $scope.tip = tip
              if (tip.comments.length > 0) {
                let lastComment = tip.comments[tip.comments.length - 1];

                if (lastComment.type === "whistleblower") {
                  statsModel.unansweredTipsCount += 1;
                }

                if (lastComment.type === "receiver" && (tip.label.length > 0 || tip.wbfiles.length > 0 || tip.status !== 'opened')) {
                  statsModel.receiverCount++
                }
              }

              statsModel.recipients.push({
                reportId: tip.progressive,
                recipients: tip.receivers.map(receiver => receiver.name).join(' - ')
              });

              $scope.parseAnswers(tip);
              $scope.initializeStaticData();
              resolve();
            });
          });

          promises.push(promise);
        }

        let lastAccessDate = new Date(tip.last_access);

        statsModel.statusLabelCount[tip.submissionStatusStr] = (statsModel.statusLabelCount[tip.submissionStatusStr] || 0) + 1;

        const creationDateObj = new Date(tip.creation_date);
        const monthYear = `${creationDateObj.toLocaleString('default', { month: 'long' })} ${creationDateObj.getFullYear()}`;
        const reportCreationDate = new Date(tip.creation_date);
        const reportUpdateDate = new Date(tip.update_date);

        const closureTime = reportUpdateDate - reportCreationDate;
        statsModel.reportCountPerMonth[monthYear] = (statsModel.reportCountPerMonth[monthYear] || 0) + 1;

        if (lastAccessDate.getTime() !== creationDate.getTime())
            statsModel.reciprocatingWhistleBlower++;

        if (tip.tor)
            statsModel.torCount++;

        if (tip.submissionStatusStr === "Closed") {
          statsModel.averageClosureTime += closureTime;
          statsModel.totalClosedTips++;
        }

        const label = tip.label;
        if (label) {
          statsModel.allLabeledCount+=1
          const words = label.split(" ").filter(word => word.length > 0);
          const labeledWords = words.filter(word => word[0] === "$");

          if (labeledWords.length == 0){
            statsModel.unlabeledCount += 1;
          }
          statsModel.labeledCountDefault += labeledWords.length;

          labeledWords.forEach(word => {
            statsModel.labelCounts[word] = (statsModel.labelCounts[word] || 0) + 1;
          });
        } else {
          statsModel.unlabeledCount++;
          statsModel.unlabeledCountDefault++;
        }
      }

      Promise.all(promises).then(function() {
        $scope.generateAnswersGraph();
      });
    };

    $scope.generateGeneralGraph = function () {
      let statusPercentages = Object.keys(statsModel.statusLabelCount).map(status => {
        const count = statsModel.statusLabelCount[status];
        const percentage = (statsModel.totalReports !== 0) ? ((count / statsModel.totalReports) * 100).toFixed(2) : 0;
        return { status, count, percentage };
      });

      statusPercentages.sort((a, b) => a.status.toLowerCase().localeCompare(b.status.toLowerCase()));
      statusPercentages.unshift({
        status: 'Total Reports',
        count: statsModel.totalReports,
        percentage: statsModel.totalReports !== 0 ? "100" : "0.00"
      });

      const labels = statusPercentages.map(item => `${item.status} | ${item.percentage} %`);
      const data = statusPercentages.map(item => item.count);

      if ($scope.statusBarChart) {
        $scope.statusBarChart.data.labels = labels;
        $scope.statusBarChart.data.datasets[0].data = data;
        $scope.statusBarChart.update();
      } else {
        $scope.statusBarChart = Statistics.generateBarGraph('statusBarChart', labels, 'General Statistics', data, 'Number of Reports', 'Status');
      }
    };

    $scope.generateInteractionLineGraph = function () {
      statsModel.averageClosureTime = (statsModel.averageClosureTime !== 0) ? ((statsModel.averageClosureTime / statsModel.totalClosedTips) / (1000 * 60 * 60 * 24)).toFixed(3) : 0;

      const labels = Object.keys(statsModel.reportCountPerMonth);
      const reportData = Object.values(statsModel.reportCountPerMonth);

      if ($scope.perMonthLineGraph) {
        $scope.perMonthLineGraph.data.labels = labels;
        $scope.perMonthLineGraph.data.datasets[0].data = reportData;
        $scope.perMonthLineGraph.update();
      } else {
        $scope.perMonthLineGraph = Statistics.generateLineGraph('perMonthLineGraph', labels, 'Interaction Statistics', reportData, 'Month', 'Reports');
      }
    };

    $scope.generateLabelGraph = function () {
      let totalItemCount = statsModel.totalReports;

      angular.forEach(statsModel.labelCounts, function (count, label) {
        let percentage = (count / totalItemCount) * 100;
        statsModel.labelCounts[label] = {
          count: count,
          percentage: percentage.toFixed(2) + "%"
        };
      });

      let unlabeledPercentage = (statsModel.unlabeledCount / totalItemCount) * 100;
      statsModel.unlabeledCount = {
        count: statsModel.unlabeledCount,
        percentage: unlabeledPercentage.toFixed(2) + "%"
      };

      let labelCountsData = Object.values(statsModel.labelCounts).map(function (label) {
        return label.count;
      });

      let unlabeledCountData = statsModel.unlabeledCount.count;
      let labels = ['Total Reports', ...Object.keys(statsModel.labelCounts), 'Unlabeled'];
      let data = [statsModel.totalReports, ...labelCountsData, unlabeledCountData];

      if ($scope.labelCountsChart) {
        $scope.labelCountsChart.data.labels = labels;
        $scope.labelCountsChart.data.datasets[0].data = data;
        $scope.labelCountsChart.update();
      } else {
        $scope.labelCountsChart = Statistics.generateBarGraph('labelCountsChart', labels, 'Labels Statistics', data, 'Number of Reports', 'Label');
      }
    };

    $scope.generateAnswersGraph = function () {
      const sortedOptions = dropdownOptions.slice().sort((a, b) => a.optionLabel.localeCompare(b.optionLabel));
      const labels = ['Total Reports', ...sortedOptions.map(entry => entry.optionLabel)];
      const tooltip = ['Total Report', ...sortedOptions.map(entry => entry.question)];
      const data = [statsModel.totalReports, ...sortedOptions.map(entry => entry.count)];

      if ($scope.channelCountsChart) {
        $scope.channelCountsChart.data.labels = labels;
        $scope.channelCountsChart.data.datasets[0].data = data;
        $scope.channelCountsChart.options.plugins.tooltip = {
          callbacks: {
            title: function (context) {
              const dataIndex = context[0].dataIndex;
              return tooltip[dataIndex];
            }
          }
        };
        $scope.channelCountsChart.update();
      } else {
        $scope.channelCountsChart = Statistics.generateBarGraph('dropdownOptionsChart', labels, 'Statistics', data, 'Number of Reports', 'DropdownOptions');
      }
    };

    $scope.initializeStaticData = function () {

      const totalReports = statsModel.totalReports;
      const statPercentageCalculator = (value, totalvalue) => (!totalvalue ? 0 : ((value / totalvalue) * 100).toFixed(2) + " %");

      const submissionStatus = {
        label: ['Total', 'New', 'Opened', 'Closed', 'Labeled', 'Unlabeled'],
        data: [
          totalReports,
          statPercentageCalculator(statsModel.statusLabelCount["New"], totalReports),
          statPercentageCalculator(statsModel.statusLabelCount["Opened"], totalReports),
          statPercentageCalculator(statsModel.statusLabelCount["Closed"], totalReports),
          statPercentageCalculator(statsModel.allLabeledCount, totalReports),
          statPercentageCalculator(statsModel.unlabeledCountDefault, totalReports)
        ]
      };

      const interactionStatus = {
        label: ['Total Report', 'Average closure time (Days)', 'Total Unanswered Tips', 'Number of interactions', 'Tor Connections', 'Reciprocating whistle blower'],
        data: [
          totalReports,
          statsModel.averageClosureTime,
          statsModel.unansweredTipsCount,
          statsModel.receiverCount,
          statsModel.torCount,
          statsModel.reciprocatingWhistleBlower
        ]
      };

      $scope.staticData = {
        submissionStatus: submissionStatus,
        interactionStatus: interactionStatus
      };
    };

    $scope.initialize = function () {
      $scope.flush();

      $scope.initializeTips();

      $scope.initializeStaticData();
      $scope.generateGeneralGraph();
      $scope.generateInteractionLineGraph();
      $scope.generateLabelGraph();
    };

    $scope.parseAnswers = function (tip) {

      tip.questionnaires.forEach((item) => {
        item.steps.forEach((step) => {
          step.children.forEach((children) => {
            if (children.statistics === true) {
              if (["selectbox", "multichoice", "checkbox"].includes(children.type)) {
                Statistics.parseStaticAnswers(tip, item, children);
              } else if (["textarea", "inputbox", "date", "daterange"].includes(children.type)) {
                Statistics.parseTextualAnswers(tip, item, children);
              }
            }
          });
        });
      });
    };

    $scope.export = function () {
      Statistics.export(answerArray, statsModel.reports, statsModel.recipients);
    };

    $scope.initialize();
  }
]);
