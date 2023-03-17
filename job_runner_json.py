import subprocess
import os
import json
import argparse
import shutil
from os.path import exists

# 
# Ensure Zowe can be found on windows machines
#
zowe_extension = ""
if os.name == 'nt':
    zowe_extension = ".cmd"
zowe = "zowe" + zowe_extension

maxrc_exceeded = False
temp_dir = "tmp"
dataset_extension = ".run"


def dataset_exists(dataset):
    #print("Exists:", dataset)
    cmd = 'zowe files ls ds "{}" --rfj'.format(dataset)
    output = run_command(cmd, bypass_error=True)
    #print("CHECK OUT:", output)
    for ds in output['data']["apiResponse"]["items"]:
        if ds['dsname'] == dataset.upper():
            return True
    return False
    
#
# Run the command, if it fails put the output on screen
# Output is in JSON format
#
def run_command(command, bypass_error=False):
    #print("BYPASS:", bypass_error)
    try:
        #print("CMD:", command)
        cmd = command.replace("zowe", zowe).split(" ")
        output = json.loads(subprocess.check_output(cmd))
    except Exception as e:
        if bypass_error:
            return output
        print("Error executing command:" ," ".join(cmd), "\nOutput is below: \n")
        print(json.loads(e.output.decode("utf-8")))
        exit(8)
    return output

def copy_dataset(dataset):
    #print("COPY DATASET:", dataset)
    create_cmd = "zowe files create pds {} --rfj".format(dataset+dataset_extension)
    run_command(create_cmd)
    source_cmd = "zowe files download am {} -d {} --rfj".format(dataset,temp_dir)
    run_command(source_cmd)
    dest_command = "zowe files upload dtp {} {} --rfj".format(temp_dir, dataset+dataset_extension)
    run_command(dest_command)

def del_dataset(dataset):
    cmd = 'zowe files delete ds "{}" -f --rfj'.format(dataset)
    run_command(cmd)
    
#
# submit the job, check for return code
#
def submit_job(ds_name, output_dir, maxrc):
    global maxrc_exceeded
    command = "zowe jobs submit data-set {} -d {} --rfj".format(ds_name, output_dir)
    zowe_output = run_command(command)
    retcode = zowe_output['data']['retcode']
    jobid = zowe_output['data']['jobid']
    if retcode.split(" ")[1] == "ERROR":
        print("Error on {} Job {} Please address job and restart".format(ds_name.upper(), jobid))
        with open("resume_job", "a") as f:
            f.write(jobid)
        exit(8)
    elif int(retcode.split(" ")[1]) > maxrc:
        print("{} Job {} return code was greater than {} so processing has stopped. Please address and restart job.".format(ds_name.upper(),jobid,maxrc))
        with open("resume_job", "a") as f:
            f.write(jobid)
        exit(8)
    print(ds_name, retcode)
    del_dataset(ds_name)

#
# Takes a list of jobs to run and submits them
#
def submit_multiple_jobs(jobs, maxrc):
    if len(jobs):
        for job in jobs:
            submit_job(job, args.output, maxrc)

#
# This gets a list of the dataset members and creates a list
# output looks like "mcqth01.jcl.ex(member)", "mcqth01.test.jcl(member)"
# This can then be passed to submit multiple jobs
#
def get_dataset_members(dataset):
    out = run_command("zowe files list am {} --rfj".format(dataset))
    #print(out["data"]["apiResponse"]["items"])
    members = ["{}({})".format(dataset, member['member']) for member in out["data"]["apiResponse"]["items"]]
    #print("MEMBERS:", members)
    return members

#
# Get the arguments for the command
#
parser = argparse.ArgumentParser()
parser.add_argument("--js", "--json", help="Dataset for jobs", required=True, dest='jsonfile')
parser.add_argument("-o","--output", help="Output directory", default="commands")
args = parser.parse_args()

data = []
try:
    with open(args.jsonfile) as json_file:
        data = json.load(json_file)
        #print(data)
except Exception as e:
    print("File {} not found".format(args.jsonfile))
    exit(8)
print("Starting")
for job in data['jobs']:
    #print("JOB:", job)
    if dataset_exists(job['name']):
        job_name = job['name']
        #print("JOB NAME:", job_name)
        jobs_to_run = get_dataset_members(job_name)
        submit_multiple_jobs(jobs_to_run, job["maxrc"])
        if maxrc_exceeded == True:
            print("Job from {} MaxRC of {} has been exceeded".format(job["name"], job["maxrc"]))
            exit(8)
        del_dataset(job_name)

if exists("temp"):
    shutil.rmtree("tmp")

print("Complete")