var express = require('express');
var async = require('async');
var { Pool } = require('pg');
var cookieParser = require('cookie-parser');
var bodyParser = require('body-parser'); // Agregada esta línea
var path = require('path'); // Agregada esta línea

var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);

var port = process.env.PORT || 4000;

io.on('connection', function (socket) {
  socket.emit('message', { text: 'Welcome!' });
  socket.on('subscribe', function (data) {
    socket.join(data.channel);
  });
});

var pool = new Pool({
  connectionString: 'postgres://postgres:postgres@db/postgres'
});

async.retry(
  { times: 1000, interval: 1000 },
  function (callback) {
    pool.connect(function (err, client, done) {
      if (err) {
        console.error("Waiting for db");
      }
      callback(err, client);
    });
  },
  function (err, client) {
    if (err) {
      return console.error("Giving up");
    }
    console.log("Connected to db");
    getDistances(client);
  }
);

function getDistances(client) {
  client.query('SELECT id, distancia FROM votes ORDER BY id', [], function (err, result) {
    if (err) {
      console.error("Error performing query: " + err);
    } else {
      var distances = result.rows[0] || { id: 0, distancia : 0 };
      io.sockets.emit("distances", JSON.stringify(distances));
    }

    setTimeout(function () {
      getDistances(client);
    }, 1000);
  });
}

app.use(cookieParser());
app.use(bodyParser.urlencoded({ extended: true })); // Agregada esta línea
app.use(bodyParser.json()); // Agregada esta línea
app.use(express.static(path.join(__dirname, '/views'))); // Modificada esta línea

app.get('/', function (req, res) {
  res.sendFile(path.resolve(__dirname, 'views', 'index.html')); // Modificada esta línea
});

server.listen(port, function () {
  console.log('App running on port ' + port);
});