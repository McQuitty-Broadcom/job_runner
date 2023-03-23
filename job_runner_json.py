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

datasets = ""
maxrc_exceeded = False
temp_dir = "tmp"
dataset_extension = ".run"
log_file = "logfile.txt"


def dataset_exists(dataset):
    cmd = f'zowe files ls ds "{dataset}" --rfj'
    output = run_command(cmd, bypass_error=True)
    for ds in output['data']["apiResponse"]["items"]:
        if ds['dsname'] == dataset.upper():
            return True
    return False
    
#
# Run the command, if it fails put the output on screen
# Output is in JSON format
#
def run_command(command, bypass_error=False):
    try:
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
    create_cmd = f"zowe files create pds {dataset+dataset_extension} --rfj"
    run_command(create_cmd)
    source_cmd = f"zowe files download am {dataset} -d {temp_dir} --rfj"
    run_command(source_cmd)
    dest_command = f"zowe files upload dtp {temp_dir} {dataset+dataset_extension} --rfj"
    run_command(dest_command)

def del_dataset(dataset):
    cmd = f'zowe files delete ds "{dataset}" -f --rfj'
    run_command(cmd)
    
#
# submit the job, check for return code
#
def submit_job(ds_name, output_dir, maxrc):
    global maxrc_exceeded
    command = f"zowe jobs submit data-set {ds_name} -d {output_dir} --rfj"
    zowe_output = run_command(command)
    retcode = zowe_output['data']['retcode']
    jobid = zowe_output['data']['jobid']
    if retcode.split(" ")[1] == "ERROR":
        msg = f"Error on {ds_name.upper()} Job {jobid}. Please address job and restart"
        print(msg)
        with open(log_file, "a") as f:
            f.write(msg)
        exit(8)
    elif int(retcode.split(" ")[1]) > maxrc:
        msg = f"{ds_name.upper()} Job {jobid} return code was greater than {maxrc} so processing has stopped. Please address and restart job."
        print(msg)
        with open(log_file, "a") as f:
            f.write(msg)
        exit(int(retcode.split(" ")[1]))
    with open(log_file, "a") as f:
        f.write(f"{ds_name} {retcode}\n")
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
    out = run_command(f"zowe files list am {dataset} --rfj")
    members = [f"{dataset}({member['member']})" for member in out["data"]["apiResponse"]["items"]]
    return members

if not exists(log_file):
    with open(log_file, "w") as f:
        f.write("\n")

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
        print(data)
except Exception as e:
    print(f"File {args.jsonfile} not found")
    exit(1)

for job in data['jobs']:
    jobs_to_run = get_dataset_members(job['name'])
    submit_multiple_jobs(jobs_to_run, job["maxrc"])
    if maxrc_exceeded == True:
        print(f'Job from {job["name"]} MaxRC of {job["maxrc"]} has been exceeded')

