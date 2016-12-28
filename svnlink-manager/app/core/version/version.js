'use strict';

angular.module('syncManager.version', [
  'syncManager.version.interpolate-filter',
  'syncManager.version.version-directive'
])

.value('version', '0.1');
