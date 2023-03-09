var cmd = require('node-cmd');
var fs = require('fs');
var config = require("./config.json");
var argv = require('yargs').argv;

const { series } = require('gulp');
 /* This function gets a list of members from the dataset */ 
function GetDSMembers(dataset, dir, callback){
    var command = `zowe files list am ${dataset} --rfj`;
    cmd.run(command, function(err, data, stderr) { 
      //log output
      var content = "Error:\n" + err + "\n" + "StdErr:\n" + stderr + "\n" + "Data:\n" + data;
      writeToFile(dir, content);
      
      if(err){
        callback(err);
      } else if (stderr){
        callback(new Error("\nCommand:\n" + command + "\n" + stderr + "Stack Trace:"));
      } else {
        //return just the members
        var datasets = JSON.parse(data).data.apiResponse.items;
        callback(datasets);
      }
    });
  }


/**
* Submits job, verifies successful completion, stores output
* @param {string}           ds                  data-set to submit
* @param {string}           [dir="job-archive"] local directory to download spool to
* @param {number}           [maxRC=0]           maximum allowable return code
* @param {awaitJobCallback} callback            function to call after completion
*/
function submitJobAndDownloadOutput(ds, dir="job-archive", maxRC=0, callback){
    var command = `zowe jobs submit data-set "${ds}" -d ${dir} --rfj`;
    cmd.run(command, function(err, data, stderr) { 
      //log output
      var content = "Error:\n" + err + "\n" + "StdErr:\n" + stderr + "\n" + "Data:\n" + data;
      writeToFile("command-archive/job-submission", content);
  
      if(err){
        callback(err);
      } else if (stderr){
        callback(new Error("\nCommand:\n" + command + "\n" + stderr + "Stack Trace:"));
      } else {
        data = JSON.parse(data).data;
        retcode = data.retcode;
  
        //retcode should be in the form CC nnnn where nnnn is the return code
        if (retcode.split(" ")[1] <= maxRC) {
          callback(null);
        } else {
          callback(new Error("Job did not complete successfully. Additional diagnostics:" + JSON.stringify(data,null,1)));
        }
      }
    });
  }

/**
* Writes content to files
* @param {string}           dir     directory to write content to
* @param {string}           content content to write
*/
function writeToFile(dir, content) {
    // Adjusted to account for Windows filename issues with : in the name.
    var d = new Date(), 
      fileName = d.toISOString().split(":").join("-") + ".txt",
      filePath = dir + "/" + fileName;
  
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    };
    
    fs.writeFileSync(filePath, content, function(err) {
      if(err) {
        return console.log(err);
      }
    });
  }

function submitMultipleJobs(jobs, callback) {
  if(jobs.length>0) {
    submitJobAndDownloadOutput(`${argv.ds}(${jobs[0].member})`, "jobs", argv.maxrc, function(err) {
      if (err) {
        callback(err);
      } else {
        jobs.shift();
        submitMultipleJobs(jobs, callback);
      }
    });
  } else {
    callback();
  }
};

/* This function would work on multiple files listed within the config file */
function defaultTask(callback) {
  if(argv.ds === undefined) {
    callback(new Error("Dataset not provided, use --ds <dsname>"));
  } else if(argv.dir === undefined) {
    callback(new Error("Output directory not provided, use --dir <dirname>"));
  } else if(argv.maxrc === undefined) {
    callback(new Error("Max Return Code not provided, use --maxrc <maxcode>"));
  } else {
    GetDSMembers(argv.ds, argv.dir, function(datasets){
        submitMultipleJobs(datasets, function(err) {
          if (err) {
            callback(err);
          } else {
            callback();
          }
        });
      });
  }
}

exports.default = defaultTask
