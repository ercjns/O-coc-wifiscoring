// meet results webv2
// Eric Jones for COC Tech Team
// December 2014

// Pieces adapated from https://github.com/azat-co/hackhall (MIT License)
// This work licensed under the MIT License



var express = require('express'),
  routes = require('./routes'),
  path = require('path'),
  favicon = require('serve-favicon'),
  logger = require('morgan'),
  bodyParser = require('body-parser'),
  multer = require('multer');


var app = express();

// app.set('port', process.env.PORT || 3000 );

// using jade for frontend engine
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');


app.use(favicon(path.join(__dirname, '/public/favicon.ico')));
app.use(logger('dev'));
app.use(bodyParser.json({type: '*/json'}));
app.use(bodyParser.urlencoded({ extended: false }));
app.use(multer({ dest: './temp'}));
app.use(express.static(path.join(__dirname, '/public')));




// middleware to log errors from HackHall Example
function logErrors(err, req, res, next) {
  console.error('logErrors', err.toString());
  next(err);
}

function clientErrorHandler(err, req, res, next) {
  console.error('clientErrors ', err.toString());
  res.send(500, { error: err.toString()});
  if (req.xhr) {
    console.error(err);
    res.send(500, { error: err.toString()});
  } else {
    next(err);
  }
}

function errorHandler(err, req, res, next) {
  console.error('lastErrors ', err.toString());
  res.send(500, {error: err.toString()});
}
//does this need to go after the 404 handler??
app.use(logErrors);
app.use(clientErrorHandler);
app.use(errorHandler);





// middleware to connect to the database from HackHall Example
var dbUrl = process.env.MONGOHQ_URL || 'mongodb://localhost/test';
var mongoose = require('mongoose');
var connection = mongoose.createConnection(dbUrl);
connection.on('error', console.error.bind(console, 'connection error:'));
connection.once('open', function () {
  console.info('connected to database')
});


// middleware to pass the collections to the relevant paths as needed
var models = require('./models');
function db (req, res, next) {
  req.db = {
    Org: connection.model('Org', models.Org, 'orgs'),
    Race: connection.model('Race', models.Race, 'races'),
    Punch: connection.model('Punch', models.Punch, 'punches'),
    Result: connection.model('Result', models.Result, 'results'),
    Runner: connection.model('Runner', models.Runner, 'runners')
  };
  return next();
}




//MAIN
app.get('/', db, routes.main.index)
app.get('/results', db, routes.main.getResults)
app.get('/results/:race', db, routes.main.getRaceResults)
// app.get('/results/:race/splittimes', db, routes.main.getRaceSplits)
app.get('/results/:race/teams', db, routes.main.getRaceTeamscores)
app.get('/team/:abbr', db, routes.main.getTeamSummary)

//ORGS
app.get('/api/orgs/:abbr', db, routes.orgs.getOrg)
app.get('/api/orgs', db, routes.orgs.getOrgs)
app.post('/api/orgs', db, routes.orgs.postOrgs)
app.put('/api/orgs/:abbr', db, routes.orgs.updateOrg)
app.delete('/api/orgs/:abbr', db, routes.orgs.delOrg)

//RACES
app.get('/api/races/:code', db, routes.races.getRace)
app.get('/api/races', db, routes.races.getRaces)
app.post('/api/races', db, routes.races.postRaces)
app.put('/api/races/:code', db, routes.races.updateRace)
app.delete('/api/races/:code', db, routes.races.delRace)

//DOWNLOADS
app.get('/api/downloads', db, routes.downloads.getDownloads)
app.post('/api/downloads', db, routes.downloads.postDownload) //handle all here?
app.delete('/api/downloads/:id', db, routes.downloads.delDownload)




// catch all remaining 'get' routes and send back a 404.
app.get('*', function(req,res){
  res.status(404).send('Error: 404 (Not Found)');
});

module.exports = app;
