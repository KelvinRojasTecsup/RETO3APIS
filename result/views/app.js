var app = angular.module('catsvsdogs', []);
var socket = io.connect();

app.controller('statsCtrl', function ($scope) {
  $scope.distancia = 0;

  var updateDistances = function () {
    socket.on('distances', function (json) {
      var data = JSON.parse(json);
      $scope.$apply(function () {
        $scope.distancia = data.distancia;  // Mostrar solo la distancia calculada
      });
    });
  };

  var init = function () {
    document.body.style.opacity = 1;
    updateDistances();
  };

  var resetValues = function () {
    $scope.distancia = 0;
  };

  socket.on('message', function (data) {
    resetValues();
    init();
  });
});