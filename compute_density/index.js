var fs = require('fs')
var geojsonStream = require('geojson-stream')
var es = require('event-stream')
var geojsonArea = require('geojson-area')

/**
 * Process a GeoJSON file and generate a PostgreSQL
 * script to insert each feature into a database
 * @function 
 * @param {string} tablename - Name of table to create in the 
 * 		database (table should not already exist)
 * @param {string} file - Name of the input GeoJSON file
 * @param {{name : string, type : string}} schema - The schema
 * 		of the table to be created.  `name` is a column name and 
 * 		`type` is the type for that column
 * @emitRow {function} emitRow - A function that returns an array
 * 		of values corresponding to the schema of the table.
 */
function copyToDB(args){
	// Create Postgres schema
	var schema = args.schema.map(function(col){
		return col.name + ' ' + col.type
	}).join(',')
	// Comma separated string of just the column names
	var colNames = args.schema.map(function(col){
		return col.name
	}).join(',')

	console.log('SET CLIENT_ENCODING TO UTF8;')
	console.log('SET STANDARD_CONFORMING_STRINGS TO ON;')
	console.log('BEGIN;')
	console.log(`CREATE TABLE "${args.tablename}" (${schema});`)
	console.log(`COPY ${args.tablename} (${colNames}) FROM stdin;`)

	// Stream in the GeoJSON file
	var inStream = fs.createReadStream(args.file)
		.pipe(geojsonStream.parse()).pipe(es.mapSync(function(feature){
			var row = args.emitRow(feature)
			console.log(args.schema.map(function(col){
				return row[col.name]
			}).join('\t'));		
		}))
	inStream.on('end', function(){
		console.log('\\.\nCOMMIT;\n')
	})	
}

copyToDB({
	tablename : 'florida_zika',
	file : __dirname + '/../output/zika.json',
	schema : [{name : 'BLOCKID10', type : 'character varying(80)'}, {name : 'pop_per_sq_km', type : 'real'}, 
			  {name : 'zika_risk', type : 'bool'}],
	emitRow : function(feature){
		var sqMeters = geojsonArea.geometry(feature.geometry)
		return {BLOCKID10 : `${feature.properties.BLOCKID10}`, 
				pop_per_sq_km : feature.properties.POP10 / sqMeters * 1000,
				zika_risk : feature.properties.risk_zone};
	},
})