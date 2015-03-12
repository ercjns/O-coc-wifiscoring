// //MAIN
// app.get('/', db, routes.main.index)
// app.get('/results', db, routes.main.getResults)
// app.get('/results/:race', db, routes.main.getRaceResults)
// app.get('/results/:race/splittimes', db, routes.main.getRaceSplits)
// app.get('/results/:race/teams', db, routes.main.getRaceTeamscores)
// app.get('/team/:abbr', db, routes.main.getTeamSummary)


var Q = require('q')


exports.index = function(req, res, next) {
  // console.log(req.body);
  res.status(200).render('index', {
    title: 'CascadeOC WiFi',
    showDates: false
  })
}

exports.getResults = function(req, res, next) {
  // Full results list...
  // To Do: Remove / De-sort the non-"OK" status entries!
  req.db.Result.where({})
    .populate('runner')
    .populate('race')
    .sort('updated')
    .exec(function (err, results) {
    if(results) {
      //deep-populate the orgs
      req.db.Runner.populate(results, {path: 'runner.org', model: req.db.Org}, function(err, stuff) {
        if(stuff) {

          //comupte the last time the data on the server changed
          stuff.sort(function(a,b) {return b.updated - a.updated})
          dataDate = stuff[0].updated;
          var dataStale = false;
          if ((Date.now() - dataDate.getTime()) > 10*60*1000) {
            dataStale = true;
          }

          res.status(200).render('allResults',{
            data: stuff,
            title: "All Results",
            showDates: true,
            dateTime: Date(Date.now()),
            dataDateTime: dataDate,
            dataStale: dataStale
          })
        }
      }) // deep populate
    } // if results
  }) // exec
  // res.send(req.body)
}


exports.getRaceResults = function(req, res, next) {
  //FIRST check to make sure the request is for a valid race
  // if (req.params.race !in <list of races>) {return res.status(404)}


  getResultsPromise(req.db)
  .then(function(results) {
    return deepPopulateResultsPromise(req.db, results)
    .then(function(fullresults) {
      var data = filterSortAssign(fullresults, {race: req.params.race})
      if (data[0] != null) {

        //comupte the last time the data on the server changed
        results.sort(function(a,b) {return b.updated - a.updated})
        dataDate = results[0].updated;
        var dataStale = false;
        if ((Date.now() - dataDate.getTime()) > 10*60*1000) {
          dataStale = true;
        }

        var showTeamResults = false;
        if (['W2M', 'W2F', 'W3F', 'W4M', 'W5M', 'W6F', 'W6M'].indexOf(req.params.race) >= 0) {
          showTeamResults = true;
        }

        res.status(200).render('raceResults',
          {okresults: data[0],
          badresults: data[1],
          title: "Results: " + data[2],
          teamresultsurl: "/results/"+req.params.race+"/teams",
          showDates: true,
          showTeamResultsLink: showTeamResults,
          dateTime: Date(Date.now()),
          dataDateTime: dataDate,
          dataStale: dataStale
          }
        )
      } else {
        res.status(200).render('noData',
          {title: "Results: " + data[2]})
      }
    }, function(errFullResults) {console.log(errFullResults)})
  }, function(errResults) {console.log(errResults)})
  .done()

}


exports.getRaceTeamscores = function(req, res, next) {
  // compute team results magically
  getResultsPromise(req.db)
  .then(function(results) {
    return deepPopulateResultsPromise(req.db, results)
    .then(function(fullresults) {
      var data = filterSortAssign(fullresults, {race: req.params.race});
      if (data[0] == null) {
        res.status(418).send("I'm a teapot! (please try again later - I may change back into a webserver)")
      } else {

        //comupte the last time the data on the server changed
        results.sort(function(a,b) {return b.updated - a.updated})
        dataDate = results[0].updated;
        var dataStale = false;
        if ((Date.now() - dataDate.getTime()) > 10*60*1000) {
          dataStale = true;
        }

        raceName = data[0][0].race.name;

        //middle school team scores are co-ed
        if (req.params.race == 'W2M') {
          var data2 = filterSortAssign(fullresults, {race: 'W2F'})
          var msdata = data[0].concat(data2[0])
          raceName = "Middle School (co-ed)";
        }
        else if (req.params.race == 'W2F') {
          var data2 = filterSortAssign(fullresults, {race: 'W2M'})
          var msdata = data[0].concat(data2[0])
          raceName = "Middle School (co-ed)";
        }

        //get just the ok results
        if (msdata) {data = msdata}
        else {data = data[0]}

        if (data != null) {

          tresults = computeTeamResults(data);

          res.status(200).render('teamResults', {
            data: tresults,
            indresultsurl: '/results/' + req.params.race,
            title: "Team Results: " + raceName,
            showDates: true,
            dateTime: Date(Date.now()),
            dataDateTime: dataDate,
            dataStale: dataStale
          });
        } else {
          res.status(200).render('noData', {
            title: "Team Results: " + raceName
          });
        }
      }
    })
  }, function(errResults) {console.log(errResults)} )
  .done()

}

exports.getTeamSummary = function(req, res, next) {
  // display a list of all runners for a given team, sorted by race then place

  getResultsPromise(req.db)
  .then(function(results) {
    return deepPopulateResultsPromise(req.db, results)
    .then(function(fullresults) {
      var data = filterSortAssign(fullresults, {})
      if (data[0] != null) {
        //for geting last updated date:
        results.sort(function(a,b) {return b.updated - a.updated})

        var clubRunners = filterClub(data[0], req.params.abbr);
        clubRunnersNotOk = filterClub(data[1], req.params.abbr)
        clubRunners = clubRunners.concat(clubRunnersNotOk);

        if (clubRunners.length > 0) {
          clubRunners.sort(function(a,b) {
            if(a.runner.name < b.runner.name) return -1;
            if(b.runner.name < a.runner.name) return 1;
            return 0;})

          res.status(200).render('teamSummary', {
            runners: clubRunners,
            title: "Results for Team: " + clubRunners[0].runner.org.name,
            showDates: true,
            dateTime: Date(Date.now()),
            dataDateTime: results[0].updated
          })
        } else {
          res.status(200).render('noData',
          {title: "Results for Team: " + req.params.abbr})
        }
      } else {
        res.status(200).render('noData',
        {title: "Results for Team: " + req.params.abbr})
      }}, function(errFullResults) {console.log(errFullResults)})
  }, function(errResults) {console.log(errResults)})
  .done()

}



// exports.getRaceSplits = function(req, res, next) {
//   console.log(req.path);
//   console.log(req.body);
//   res.send(req.body)
// }



///////////////////////////////////////////////////////
// Individual Scoring Helper Functions
///////////////////////////////////////////////////////


function getResultsPromise(db) {
  var deferred = Q.defer();
  db.Result.find({})
    .populate('runner')
    .populate('race')
    .exec(function(err, res) {
      if(res) { deferred.resolve(res) }
      else { deferred.reject("no results?") }
    })
  return deferred.promise
}

function deepPopulateResultsPromise(db, results) {
  var deferred = Q.defer();

  data = results
  opts = {path: 'runner.org', model: db.Org}

  db.Runner.populate(data, opts, function(err, res) {
    if(res) { deferred.resolve(res) }
    else { deferred.reject("unable to populate?") }
  })
  return deferred.promise
}

function filterSortAssign(results, options) {
  //assuming that we take delta updates, recalc every load is ok (but not really)
  //retuns 3-item list:
  //   sorted list of ok status download objects
  //   list of !ok status download objects
  //   raceName

  // sort for desired race
  if ('race' in options) {
    var results = filterRace(results, options.race)
  }

  // if no finishers to rank, return now.
  if (results.length == 0) {
    return [null, null, options.race]
  }

  if ('race' in options) {
    raceName = results[0].race.name
  } else {
    raceName = 'All Races'
  }

  // filter for ok status
  var ok = filterOk(results)
  var no = filterNotOk(results)

  // sort, assign place + points
  if ('race' in options) {
    var ok = assignPoints(ok)
  }

  return [ok, no, raceName]
}

function filterRace(a, race) {
  return a.filter(function(el) {
    if (el.race.code == race) {return true}
    else {return false}
  })
}

function filterOk(a) {
  return a.filter(function(el) {
    if (el.status == 'OK') {return true}
    else {return false}
  })
}
function filterNotOk(a) {
  return a.filter(function(el) {
    if (el.status != 'OK') {return true}
    else {return false}
  })
}

function filterClub(a, club) {
  return a.filter(function(el) {
    if (el.runner.org.abbr == club) {return true}
    else {return false}
  })
}

function assignPoints(a) {
  a.sort(function(a,b) {return a.time-b.time})
  for (var i=0; i<a.length; i++) {
    if (i==0) {
      //winner!
      a[i].place = 1
      a[i].points = 100

    } else if (i==1) {
      //second place
      if (a[i].time == a[i-1].time) {
        a[i].place = a[i-1].place
        a[i].points = a[i-1].points
      } else {
      a[i].place = 2
      a[i].points = 95
      }

    } else if (i==2) {
      //third place
      if (a[i].time == a[i-1].time) {
        a[i].place = a[i-1].place
        a[i].points = a[i-1].points
      } else {
        a[i].place = 3
        a[i].points = 92
      }

    } else {
      //fourth onwards
      if (a[i].time == a[i-1].time) {
        a[i].place = a[i-1].place
        a[i].points = a[i-1].points
      } else {
        a[i].place = i + 1
        a[i].points = 93 - i
      }
    }
    a[i].save()
  }
  return a
}






///////////////////////////////////////////////////////
// Team Scoring Helper Functions
///////////////////////////////////////////////////////

function computeTeamResults(raceresults) {
  //sort by org
  raceresults.sort(function(a,b) {
    if (a.runner.org.abbr < b.runner.org.abbr) {return -1}
    else if (a.runner.org.abbr > b.runner.org.abbr) {return 1}
    else {return 0}
  })

  //create array of arrays by org.
  var raceTeams = [ [raceresults[0]] ]
  var idx = 0
  for (i=1; i<raceresults.length; i++) {
    if (raceresults[i].runner.org.abbr == raceresults[i-1].runner.org.abbr) {
      //same org
      raceTeams[idx].push(raceresults[i])
    } else {
      //different org
      idx++;
      raceTeams.push([]);
      raceTeams[idx].push(raceresults[i]);
    }
  }

  var teamResultsData = []

  //sort each inner array by points, keep top 3, calculate teamscore
  raceTeams.forEach(function(team, i){
    // always sort
    team.sort(function(a,b) {
      return (b.points - a.points)
    })
    // slice if more than three elements
    if (team.length > 3) {
      team = team.slice(0,3)
      raceTeams[i] = team
    }
    // calculate the score
    teamscore = team.reduce(function(prev, curr) {
      return prev + curr.points
    }, 0)

    // package it up
    var tdata = {
      "abbr": team[0].runner.org.abbr,
      "name": team[0].runner.org.name,
      "place": null,
      "score": teamscore
    }
    teamResultsData.push({"team": tdata, "runners": team})
  })


  sorted = assignTeamPlace(teamResultsData)

  return sorted
}

function assignTeamPlace(teams) {
  teams.sort( breakTies )

  // at this point, teams is in the proper order, but still need to determine
  // if a tie is a true tie or not, but don't need to worry about multi-way
  // ties being out of order, so a single pass through pair-wise comparison is
  // sufficient.

  teams[0].team.place = 1
  var nextplace = 2

  for (i=1; i<teams.length; i++) {
    if (teams[i].team.score != teams[i-1].team.score) {
      // score is not equal (lower), assign next place
      teams[i].team.place = nextplace;
      nextplace += 1;
    } else {
      var isTie = true
      // team scores equal, check to see if all runner scores equal (already proper sort)
      for (j=0; j<teams[i].runners.length; j++) {
        if (teams[i].runners[j].points != teams[i-1].runners[j].points) {
          isTie = false
          break
        }
      } // for all runners
      if (isTie) {
        teams[i].team.place = teams[i-1].team.place;
        nextplace += 1;
      } else {
        teams[i].team.place = nextplace;
        nextplace += 1;
      }
    } // else (scores tied)
  } // for each team.

  return teams

}

function breakTies(a,b) {
  // sorting function for teams, including team tie-break rules.

  scores = b.team.score - a.team.score
  if (scores != 0) {return scores;}

  first = b.runners[0].points - a.runners[0].points
  if (first != 0) {return first;}

  if (a.runners[1] && b.runners[1]) {
    // console.log('comparing second runners from', a.team.abbr, b.team.abbr)
    second = b.runners[1].points - a.runners[1].points
    if (second != 0) {return second;}
  } else if (a.runners[1]) {
    return -1
  } else if (b.runners[1]) {
    return  1
  }

  if (a.runners[2] && b.runners[2]) {
    // console.log('comparing third runners from', a.team.abbr, b.team.abbr)
    third = b.runners[2].points - a.runners[2].points
    if (third != 0) {return third};
  } else if (a.runners[2]) {
    return -1
  } else if (b.runners[2]) {
    return  1
  }

  return 0
}
