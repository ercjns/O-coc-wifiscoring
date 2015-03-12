// //RACES
// app.get('/api/races/:code', db, routes.races.getRace)
// app.get('/api/races', db, routes.races.getRaces)
// app.post('/api/races', db, routes.races.postRaces)
// app.put('/api/races/:code', db, routes.races.updateRace)
// app.delete('/api/races/:code', db, routes.races.delRace)

// exports.Race = new Schema({
//   series: String,
//   name: String,
//   code: String,
//   course: Number,
//   results: [{type: Schema.Types.ObjectId, ref: 'Result'}]
// });

exports.getRace = function(req, res, next) {
  var select = {code:req.params.code}

  req.db.Race.findOne(select, function(err, race) {
    if (err) return next(err);
    if (race) {
      console.log(race.series, race.code, race.name);
      res.status(200).json(race);
    } else {
      res.status(404).send('Not Found')
    }
  });
}

exports.getRaces = function(req, res, next) {
  var select = {}
  var fields = {_id:0, results:0}
  req.db.Race.find(select, fields, function(err, races) {
    if (err) return next(err);
    if (races) {
      res.status(200).json(races);
    } else {
      res.status(418).send("I'm a teapot! (Not Found)")
    }
  });
}

exports.postRaces = function(req, res, next) {
  //add new races in bulk. maybe update rather than skip??
  if (req.body.races) {
    for (i=0; i<req.body.races.length; i++) {
      (function(i) {
        req.db.Race.findOne({code: req.body.races[i].code})
        .lean().exec(function(err,result) {
          newrace = req.body.races[i]
          if (err) return next(err);
          if (result == null) {
            console.log('no match, save something')
            o = req.db.Race(newrace)
            console.log('saved this: ', o)
            o.save()
          } else {
            console.log('matched: ', newrace, result.name)
          }
        }) // findOne
      })(i) // function closure for preserve i within the async db call
    } // for loop
  } // if body.orgs
  res.status(200).json(req.body.races)
};

exports.updateRace = function(req, res, next) {
  var select = {code: req.params.code}
  var update = {series: req.body.series, name: req.body.name, course: req.body.course}
  console.log(update);
  req.db.Race.update(select, update, function(err, n, raw) {
    if (err) return next(err);
    console.log('Documents updated: ', n)
  }
) //race.update
res.status(200).send(req.body)
};

exports.delRace = function(req, res, next) {
  var select = {code: req.params.code}
  req.db.Race.findOneAndRemove(select, function(err,doc) {
    if (err) return next(err);
    console.log('removed: ', doc)
  })
  res.status(200).send(req.params.code)
};
