angular.
  module('core.devsite').
  factory('Dsite', ['$resource',
    function($resource) {
      return $resource('http://localhost:5000/api/devsites/', {}, {
        query: {
          method: 'GET',
          //params: {siteId: 'phones'},
          isArray: true
        }
      });
    }
  ]);