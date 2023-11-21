GL.controller("StatisticsCtrl", ["$scope", function ($scope) {
    $scope.charts = [];

    $scope.charts.push({
      title: "Returning whistleblowers",
      labels: ["Returning", "Not returning"],
      values: [$scope.resources.stats.reports_with_no_access, $scope.resources.stats.reports_with_at_least_one_access]
    });

    $scope.charts.push({
      title: "Anonimity",
      labels: ["Anonymous reports", "Subscribed reports", "Reports subscribed after initial anonymous contact"],
      values: [$scope.resources.stats.reports_anonymous, $scope.resources.stats.reports_subscribed, $scope.resources.stats.reports_subscribed_later]
    });
}]);
