GL.controller("FeaturesCtrl", ["$scope", "$filter", "$http", "$location", "$uibModal", "$window", "RTipExport", "TokenResource",
    function ($scope, $filter, $http, $location, $uibModal, $window, RTipExport, TokenResource) {
        console.log($scope.resources.rtips.rtips);
        console.log($scope.resources);
        console.log($scope.submission_statuses,"submission_statuses");
        // var arr = [1, 222, 3333, 'hello-world']
        // $scope.names = [];
        // var values = [
        //     { name: 'Binary Search' },
        //     { name: 'Linear Search' },
        //     { name: 'Interpolation Search' }
        // ];
        // angular.forEach(values, function (value, key) {
        //     $scope.names.push(value.name);
        // });
        var percentages = [];
        $scope.percentages = [];

        function calculatePercentageOfReports(array, status) {
            var filteredReports = array.filter(function (item) {
                return item.status === status;
            });

            var percentage = (filteredReports.length / array.length) * 100;
            return { title: status + " Reports", percentage: percentage, num: filteredReports.length };
        }

        var rtipsArray = $scope.resources.rtips.rtips;

        var percentageOfNewReports = calculatePercentageOfReports(rtipsArray, "new");
        var percentageOfOpenReports = calculatePercentageOfReports(rtipsArray, "opened");
        var percentageOfClosedReports = calculatePercentageOfReports(rtipsArray, "closed");

        // $scope.percentages.push({ title: "Reports", percentage: rtipsArray.length, num: rtipsArray.length });
        $scope.percentages.push({ title: "Reports", num: rtipsArray.length });
        $scope.percentages.push({ title: "New Reports", percentage: percentageOfNewReports.percentage, num: percentageOfNewReports.num });
        $scope.percentages.push({ title: "Open Reports", percentage: percentageOfOpenReports.percentage, num: percentageOfOpenReports.num });
        $scope.percentages.push({ title: "Closed Reports", percentage: percentageOfClosedReports.percentage, num: percentageOfClosedReports.num });
    }])