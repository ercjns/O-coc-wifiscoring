// //ORGS
// app.get('/api/orgs/:abbr', db, routes.orgs.getOrg)
// app.get('/api/orgs', db, routes.orgs.getOrgs)
// app.post('/api/orgs', db, routes.orgs.postOrgs)
// app.put('/api/orgs/:abbr', db, routes.orgs.updateOrg)
// app.delete('/api/orgs/:abbr', db, routes.orgs.delOrg)
//
// exports.Org = new Schema({
//   name: String,
//   abbr: String,
//   runners: [{type: Schema.Types.ObjectId, ref: 'Runner'}]
// });

exports.getOrg = function(req, res, next) {
  var select = {abbr:req.params.abbr}

  req.db.Org.findOne(select, function(err, org) {
    if (err) return next(err);
    if (org) {
      console.log(org.abbr, org.name);
      res.status(200).json(org);
    } else {
      res.status(404).send('Not Found')
    }
  });
}

exports.getOrgs = function(req, res, next) {
  var select = {}

  req.db.Org.find({}, function(err, orgs) {
    if (err) return next(err);
    if (orgs) {
      res.status(200).json(orgs);
    } else {
      res.status(418).send("I'm a teapot! (Not Found)")
    }
  });
}

exports.postOrgs = function(req, res, next) {
  //add new orgs in bulk. should update rather than skip??
  if (req.body.orgs) {
    for (i=0; i<req.body.orgs.length; i++) {
      (function(i) {
        req.db.Org.findOne({abbr: req.body.orgs[i].abbr})
          .exec(function(err,result) {  //removed .lean()
            neworg = req.body.orgs[i]
            if (err) return next(err);
            if (result == null) {
              console.log('NEW')
              o = req.db.Org(neworg)
              console.log('saved this: ', o)
              o.save()
            } else if (result.name != neworg.name) {
              console.log('UPDATE:', result.name, 'as', neworg.name)
              result.name = neworg.name
              result.save()
            } else {
              console.log('match:', result.abbr, result.name)
            }
        }) // findOne
      })(i) // function closure for preserve i within the async db call
    } // for loop
  } // if body.orgs
  res.status(200).json(req.body.orgs)
}



exports.updateOrg = function(req, res, next) {
  req.db.Org.update({abbr: req.params.abbr}, {name: req.body.name}, function(err, n, raw) {
    if (err) return next(err);
    console.log('Documents updated: ', n)
    }
  ) //Org.update
  res.status(200).send(req.body)
}

exports.delOrg = function(req, res, next) {
  req.db.Org.findOneAndRemove({abbr: req.params.abbr}, function(err,doc) {
    if (err) return next(err);
    console.log('removed: ', doc)
  })
  res.status(200).send(req.params.abbr)
}
