// //DOWNLOADS
// app.get('/api/downloads', db, routes.downloads.getDownloads)
// app.post('/api/downloads', db, routes.downloads.postDownload) //handle all here?
// app.delete('/api/downloads/:si', db, routes.downloads.delDownload)

// exports.Result = new Schema({
//   sicard: Number,
//   race: {type: Schema.Types.ObjectId, ref: 'Race'},
//   runner: {type: Schema.Types.ObjectId, ref: 'Runner'},
//   bib: Number,
//   time: Number,
//   status: String,
//   points: Number,
//   punches: [{type: Schema.Types.ObjectId, ref: 'Punch'}],
//   updated: Date
// });

// exports.Runner = new Schema({
//   name: String,
//   org: {type: Schema.Types.ObjectId, ref: 'Org'},
//   results: [{type: Schema.Types.ObjectId, ref: 'Result'}]
// });

// exports.Punch = new Schema({
//   control: String,
//   time: Number,
//   status: String,
//   result: {type: Schema.Types.ObjectId, ref: 'Result'},
// });

var xml2js = require('xml2js');
var fs = require('fs');
var Q = require('q');



exports.getDownloads = function(req, res, next) {
  var select = {}
  req.db.Result.find(select, {_id:0}, function(err, results) {
    //TODO:
    //rather than just dumping the result collection, this should also populate those documents
    //with the race, runner, and punch values...
    if (err) return next(err);
    if (results) {
      res.status(200).json(results);
    } else {
      res.status(418).send("I'm a teapot! (Not Found)")
    }
  });
}

exports.postDownload = function(req, res, next) {

  var fn = './temp/' + req.files.file.name;
  console.log("Post of file: " + fn);

  // read the file
  var parser = new xml2js.Parser({explicitArray: false});
  fs.readFile(fn, function(err, fdata) {
    parser.parseString(fdata, function(err, xmldata) {
      //determine what type of upload and handle as appropriate
      if (xmldata.ResultList.$.iofVersion === '3.0') {
        // Sport Software IOFv3 results export
        console.log('Processing Sport Software IOFv3 Results')
        opts = {'IOFv': 3};

        // TODO: Don't do this!!!!
        // need to not delete so that we can preserve registration data
        // in order to sync IDs from start box telemetry with names/clubs

        // Delete Everything :(
        emptyCollections(req.db)

        // Process each ClassResult

        // Expecting list of objects. fails if only one class?
        compclasses = xmldata.ResultList.ClassResult
        compclasses.forEach(function(compclass) {
          // Process each PersonResult
          for (i=0; i<compclass.PersonResult.length; i++) {
            (function(i) {
              p = compclass.PersonResult[i].Person;
              o = compclass.PersonResult[i].Organisation;
              r = compclass.PersonResult[i].Result;
              c = compclass.Class.ShortName;

              (function(o,p,r,c) {
                var runnerName = flattenName(opts,p)

                getOrgPromise(req.db, o.ShortName)
                .then(function(org) {
                  return saveRunnerPromise(req.db, runnerName, org)
                  .then(function(runner) {
                    return getRacePromise(req.db, c)
                    .then(function(race) {
                      return saveResultPromise(opts, req.db, runner, race, r)
                    }, function(errRace) {console.log(errRace,c)} )
                  }, function(errRunner) {console.log(errRunner)} )
                }, function(errOrg) {console.log(errOrg, o.ShortName)} )
                .done()
              })(o,p,r,c) // immediately execute
            })(i) // each PersonResult
          }
        }) // each CompClass
        console.log('Done refreshing db')
      } // end IF IOFv:3


      else if (xmldata.ResultList.$.status === 'snapshot' &&
          xmldata.ResultList.IOFVersion.$.version === '2.0.3') {
        // OORG IOFv2 results export
        console.log('Processing an OORG snapshot')

        opts = {'IOFv': 2};

        // To do: delete the entire database, sorry..
        // delete all punches, results, and runners
        // empty the results list from each race
        // empty the runners list from each org
        emptyCollections(req.db)


        // To Do: handle cases where runner already exists (what is current behavior?)
        // To Do: handle cases where saving runner or result fails (retry but don't hang)

        compclasses = xmldata.ResultList.ClassResult
        compclasses.forEach(function(compclass) {
          for (i=0; i<compclass.PersonResult.length; i++) {
            (function(i) {
              p = compclass.PersonResult[i].Person;
              r = compclass.PersonResult[i].Result;
              c = compclass.ClassShortName;
              (function(p,r,c) {

                var runnerName = flattenName(opts, p)

                getOrgPromise(req.db, p.CountryId)
                .then(function (org) {
                  return saveRunnerPromise(req.db, runnerName, org)
                  .then(function(runner) {
                    return getRacePromise(req.db, c)
                    .then(function(race) {
                      return saveResultPromise(opts, req.db, runner, race, r)
                      .then(function(result) {
                        saveSplitTimes(opts, req.db, result, r.SplitTime)
                      })
                    }, function(errRace) {console.log(errRace, c)} )
                  }, function(errRunner) {console.log(errRunner)} )
                }, function(errOrg) {console.log(errOrg, p.CountryId)} )
                .done()

              })(p,r,c) // immediately execute function to save data
            })(i) // immedieatly execute loop
          } // for personresult.length
        }) // for each compclass
        console.log("Done refreshing database")
      } // if status:snapshot && IOFv:2



      else if (xmldata.ResultList.$.status === 'delta') {

        console.log('Processing a delta update')
        // note that deltas use v3.0
        opts = {'IOFv': 3}

        compclass = xmldata.ResultList.ClassResult
        p = compclass.PersonResult.Person
        o = compclass.PersonResult.Organisation
        r = compclass.PersonResult.Result
        c = compclass.Class.Name

        // TO DO: this function should update rather than blindly adding new records?

        getOrgPromise(req.db, o.ShortName)
        .then(function (org) {
          return saveRunnerPromise(req.db, p.Name.Given, org)
          .then(function(runner) {
            return getRacePromise(req.db, c)
            .then(function(race) {
              return saveResultPromise(opts, req.db, runner, race, r)
              .then(function(result) {
                saveSplitTimes(opts, req.db, result, r.SplitTime)
              })
            }, function(errRace) {console.log(errRace, c)} )
          }, function(errRunner) {console.log(errRunner)} )
        }, function(errOrg) {console.log(errOrg, o.ShortName)} )
        .then(console.log("Done adding record"))
        .done()

      } // if status:delta









      else if (xmldata.ResultList.$.status === 'complete') {
        console.log('Processing a final results update')

        // wipe the database, then replace with new data
        // or really, soft delete, import, then hard delete
        // or just soft delete everything. requires abilty
        // to soft delete. not sure if that's baked in.

      } // if status:complete

      else {
        console.log('unrecognized')
      }


    }) // parser
    fs.unlink(fn, function(err) {
      console.log('deleted the upload file: ', fn)
    }) // unlink temp upload
  }) // read file


  // search the database for matches

  // if no match, create new records

  // if match found, update it with new/altered info (persist where no info provided)


  res.send("Posted")
} //postDownload


exports.delDownload = function(req, res, next) {
  console.log(req.path);
  console.log(req.body);
  res.send(req.body)
}

//////////////////////////////////////
// Helper and Formatting functions
//////////////////////////////////////

function MMSStoSec(stime) {
  t = stime.split(":");
  result = (parseInt(t[0]) * 60) + parseInt(t[1]);
  return result
}

function SectoMMSS(inttime) {
  m = Math.floor(inttime / 60)
  s = inttime % 60
  if (s>=0 && s <10) {
    s = "0" + s
  }
  return m + ":" + s
}

function flattenName(opts, p) {
  //TODO: make this more clever? Also replace '_' with ' '.
  var n = '';
  if (opts.IOFv == 2) {
    if (p.PersonName.Given != null) { n += p.PersonName.Given }
    if (n.length > 0) { n += ' ' }
    if (p.PersonName.Family != null) { n += p.PersonName.Family }
    return n
  } else if (opts.IOFv == 3) {
    if (p.Name.Given != null) { n += p.Name.Given }
    if (n.length > 0) { n += ' ' }
    if (p.Name.Family != null) { n += p.Name.Family }
    return n
  }
}

function emptyCollections(db) {
  // delete all punches, results, and runners
  db.Punch.remove({}, function(err,data) {
    if(err) {console.log(err)}
    console.log("Removed all Punches (async)")
  })
  db.Result.remove({}, function(err,data) {
    if(err) {console.log(err)}
    console.log("Removed all Results (async)")
  })
  db.Runner.remove({}, function(err,data) {
    if(err) {console.log(err)}
    console.log("Removed all Runners (async)")
  })

  // empty the results list from each race
  q = {}
  u = {$set: {results: []} }
  o = {multi: true}
  db.Race.update(q, u, o, function(err,data) {
    if(err) {console.log(err)}
    console.log("Cleared results from races (async)")
  })

  // empty the runners list from each org
  q = { }
  u = {$set: {runners: []} }
  o = {multi: true}
  db.Org.update(q, u, o, function(err,data) {
    if(err) {console.log(err)}
    console.log("Cleared runners from orgs (async)")
  })
}

//////////////////////////////////////
// Promise functions...
//////////////////////////////////////

function getOrgPromise(db, sabbr) {
  // console.log("getOrgPromise for org: ", sabbr);
  var deferred = Q.defer();

  db.Org.findOne({abbr: sabbr}).exec(function(err, data) {
    if (data) {
      //return the data in the promise
      deferred.resolve(data)
    } else {
      //if no org found - create it!
      console.log('saving unknown org: ', sabbr)
      o = new db.Org
      o.abbr = sabbr
      o.name = sabbr + " - Unknown"
      // console.log(o)
      o.save()

      deferred.resolve(o)
      // deferred.reject('no org found', sabbr)
    }
  })
  return deferred.promise
} //getOrgPromise

function saveRunnerPromise(db, sname, org) {
  //org may be null! (or maybe not...)
  var deferred = Q.defer();
  var runner = new db.Runner;
  runner.name = sname;
  runner.org = org._id;
  // console.log(runner)
  runner.save()

  org.runners.push(runner._id)
  org.save()

  deferred.resolve(runner);
  return deferred.promise
}

function getRacePromise(db, c) {
  var deferred = Q.defer();
  db.Race.findOne({code: c}).exec(function(err, data) {
    if (data) {
      //return the data in the promise
      deferred.resolve(data)
    } else {
      //if no data, reject the promise
      deferred.reject('no race found', c)
    }
  })
  return deferred.promise
} //getRacepromise


function saveResultPromise(opts, db, runner, race, info) {
  var deferred = Q.defer();

  if (opts.IOFv == 2){
    var result = new db.Result;
      result.sicard = null
      result.race = race._id
      result.runner = runner._id
      result.bib = info.BibNumber
      if (info.Time) {
        result.time = MMSStoSec(info.Time._)
        result.timestr = info.Time._
      }
      result.status = info.CompetitorStatus.$.value
      result.points = null
      result.punches = null
      result.updated = Date.now()
  } else if (opts.IOFv == 3){
    var result = new db.Result;
      result.sicard = info.ControlCard
      result.race = race._id
      result.runner = runner._id
      result.bib = info.BibNumber
      if (info.Time) {
        result.time = info.Time
        result.timestr = SectoMMSS(info.Time)
      }
      result.status = info.Status
      result.points = null
      result.punches = null
      result.updated = Date.now()
  }

  // console.log(result)
  result.save()

  runner.results.push(result._id)
  runner.save()
  race.results.push(result._id)
  race.save()

  deferred.resolve(result)
  return deferred.promise
}

function saveSplitTimes(opts, db, result, splits) {
  splits.forEach(function(split) {
    var punch = new db.Punch;
    punch.control = split.ControlCode //String
    punch.result = result._id
    if (opts.IOFv == 2) {
      if (split.Time._) {
        punch.status = "OK"
        punch.time = MMSStoSec(split.Time._)
      } else {
        punch.status = "MISSING"
      }
    } else if (opts.IOFv == 3) {
      punch.time = split.Time
      punch.status = split.Status
    }
    // console.log(punch)
    punch.save()
  }) // forEach split
}
