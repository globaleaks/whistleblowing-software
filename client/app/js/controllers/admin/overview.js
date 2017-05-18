GLClient.controller('AdminOverviewCtrl', ['$scope', function($scope){
  $scope.tabs = [
    {
      title:"Stats",
      template:"views/admin/overview/tab1.html"
    },
    {
      title:"Activities",
      template:"views/admin/overview/tab2.html"
    },
    {
      title:"Submissions",
      template:"views/admin/overview/tab3.html"
    },
    {
      title:"Users",
      template:"views/admin/overview/tab4.html"
    },
    {
      title:"Files",
      template:"views/admin/overview/tab5.html"
    },
    {
      title:"Anomalies",
      template:"views/admin/overview/tab6.html"
    },
    {
      title:"Scheduled jobs",
      template:"views/admin/overview/tab7.html"
    }
  ];
}]);
