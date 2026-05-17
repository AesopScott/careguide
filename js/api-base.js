(function () {
  var host = (window.location && window.location.hostname) || '';
  var STAGE_API = 'https://careguide-api-stage-658340465706.us-central1.run.app';
  var PROD_API  = 'https://careguide-api-658340465706.us-central1.run.app';
  window.API_BASE = host.indexOf('stage.') === 0 ? STAGE_API : PROD_API;
})();
