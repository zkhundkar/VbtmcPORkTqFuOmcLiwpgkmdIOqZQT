'use strict';

// Declare app level module which depends on views, and components
angular.module('syncManager', [
  'ngRoute',
//  'syncManager.version'
])
.service('pagerService', PagerService)
.controller('PageCtrl', PagerController)
.controller('AppCtrl', AppCtrl)
.controller('AlertsCtrl', AlertsController)
.filter('page', PageFilterFactory)

.config(['$locationProvider', '$routeProvider', function($locationProvider, $routeProvider) {
	$locationProvider.hashPrefix('!');

	$routeProvider
	// Home
	.when("/home", {template: "<home-view></home-view>" })
	.when("/apps", {template: "<app-select></app-select>" })
	// Pages
	.when("/devsites", {template: '<devsites-list></devsites-list><p> </p>' })
	.when("/repos", {template: '<repo-list></repo-list>'})
	.when("/alerts", {templateUrl: "alerts/alerts.html"})
	//.when("/alerts", {templateUrl: "hello/hello.html"})
	/* etc… routes to other pages… */
	  
	  .otherwise({redirectTo: '/'});
	}]);

AppCtrl.$inject = ['$scope', '$location' ]
function AppCtrl($scope, $location) {
	$scope.navitems = [
	{ name : "home", active : "active", ptext : "Home" },
	{ name : "devsites", active : "",  ptext : "Dev Sites" },
	{ name : "repos", active : "",  ptext : "Repos" },
	{ name : "apps", active : "",  ptext : "Applications" },
	{ name : "alerts", active : "",  ptext : "Alerts" }
	
	];
	$scope.isActive = function(currentpage) { if (currentpage == '/home') {return $location.path() == '/' } ;
	return currentpage == $location.path() };
};

AlertsController.$inject = ['$scope'];
function AlertsController($scope) {
	//var self = this;
	$scope.active = 1;
	$scope.auth_key = "supercalifragilisti";
	$scope.system_id = '5499';
	$scope.remote_ip = '5499';
	$scope.port = '8450';
	$scope.host_string = 'ialert2.iatric.com/ialert/ialert.asmx';
	$scope.client_type = '2';
	$scope.client_ver = '5.66';
	$scope.port = '8450';

}

PagerController.$inject = ['pagerService', 'pageFilter'];
function PagerController(PagerService, pageFilter) {
	var vm = this;

	vm.pager = {};
	vm.setPage = setPage;
	vm.nextPage = nextPage;
	vm.prevPage = prevPage;
	
	initController();

	function initController(itemcount) {
		var items = itemcount ? itemcount : 1;
		// initialize to page 1
		vm.setPage(1, items);
	}
	function firstPage() {
		// initialize to page 1
		vm.setPage(1, vm.pager.totalItems);
	}
	function prevPage() {
		// initialize to page 1
		vm.setPage(vm.pager.currentPage - 1 || 1, vm.pager.totalItems);
	}
	function nextPage() {
		// initialize to page 1
		vm.setPage(vm.pager.currentPage + 1, vm.pager.totalItems);
	}
	function lastPage() {
		// initialize to page 1
		vm.setPage(vm.pager.totalPages, vm.pager.totalItems);
	}
	function setPage(page, itemcount, pagesize) {
		if (page < 1 || page > vm.pager.totalPages) {
			return;
		}
		// get pager object from service
		var pgsz = pagesize || vm.pager.pageSize || 10;
		var itemsz = itemcount || vm.pager.totalItems;
		
		vm.pager = PagerService.GetPager(itemsz, page, pgsz);
		
		// get current page of items
		vm.items = [...Array(vm.pager.endIndex-vm.pager.startIndex+1).keys()].map(function (x) {return x+vm.pager.startIndex;}, 1);;
	}
};

function PageFilterFactory() {
	return function(input, startFrom) {
		// filter logic
		try {
			return  input.slice(startFrom);
		}
		catch (e) { return input; }//filteredOutput;
	};
};


function PagerService() {
	// service definition
	var service = {};

	service.GetPager = GetPager;

	return service;

	// service implementation
	function GetPager(totalItems, currentPage, pageSize) {
		// default to first page
		currentPage = currentPage || 1;

		// default page size is 10
		pageSize = Number(pageSize) || 10;

		// calculate total pages
		var totalPages = Math.ceil(totalItems / pageSize);

		var startPage, endPage;
		if (totalPages <= 10) {
			// less than 10 total pages so show all
			startPage = 1;
			endPage = totalPages;
		} else {
			// more than 10 total pages so calculate start and end pages
			if (currentPage <= 6) {
				startPage = 1;
				endPage = 10;
			} else if (currentPage + 4 >= totalPages) {
				startPage = totalPages - 9;
				endPage = totalPages;
			} else {
				startPage = currentPage - 5;
				endPage = currentPage + 4;
			}
		}

		// calculate start and end item indexes
		var startIndex = (currentPage - 1) * pageSize;
		var tempendIndex = startIndex + pageSize - 1;
		var endIndex = Math.min(tempendIndex, totalItems - 1);

		// create an array of pages to ng-repeat in the pager control
		var pages = [...Array(endPage-startPage+1).keys()].map(function (x) {return x+startPage;}, 1);

		// return object with all pager properties required by the view
		return {
			totalItems: totalItems,
			currentPage: currentPage,
			pageSize: pageSize,
			totalPages: totalPages,
			startPage: startPage,
			endPage: endPage,
			startIndex: startIndex,
			endIndex: endIndex,
			pages: pages
		};
	}
}