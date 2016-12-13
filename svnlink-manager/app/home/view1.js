'use strict';

angular.module('syncManager')

  .component('homeView', {
		templateUrl: 'home/view1.html',		
		
		controller: function HomeCtrl($http) {
			self = this;
			self.revtime = '-ts';
			$http.get("http://localhost:5000/api/runlog").then(function(response) {
			self.runlog = response.data;
		})}
  });