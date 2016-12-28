'use strict';

describe('syncManager.version module', function() {
  beforeEach(module('syncManager.version'));

  describe('version service', function() {
    it('should return current version', inject(function(version) {
      expect(version).toEqual('0.1');
    }));
  });
});
