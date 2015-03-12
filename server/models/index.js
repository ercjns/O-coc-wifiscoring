// meet results webv2
// Eric Jones for COC Tech Team
// December 2014

// Pieces adapated from https://github.com/azat-co/hackhall (MIT License)
// This entire work licensed under the MIT License



var mongoose = require('mongoose');
var Schema = mongoose.Schema;


exports.Org = new Schema({
	name: String,
	abbr: String,
	runners: [{type: Schema.Types.ObjectId, ref: 'Runner'}]
});


exports.Race = new Schema({
	series: String,
	name: String,
	code: String,
	course: Number,
	results: [{type: Schema.Types.ObjectId, ref: 'Result'}]
});


exports.Punch = new Schema({
		control: String,
		time: Number,
		status: String,
		result: {type: Schema.Types.ObjectId, ref: 'Result'},
});


exports.Result = new Schema({
		sicard: Number,
		race: {type: Schema.Types.ObjectId, ref: 'Race'},
		runner: {type: Schema.Types.ObjectId, ref: 'Runner'},
		bib: Number,
		time: Number,
		timestr: String,
		status: String,
		points: Number,
		place: Number,
		punches: [{type: Schema.Types.ObjectId, ref: 'Punch'}],
		updated: Date
});


exports.Runner = new Schema({
	name: String,
	org: {type: Schema.Types.ObjectId, ref: 'Org'},
	results: [{type: Schema.Types.ObjectId, ref: 'Result'}]
});
