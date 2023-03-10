import subprocess
import os
import json
import argparse

# 
# Ensure Zowe can be found on windows machines
#
zowe_extension = ""
if os.name == 'nt':
    zowe_extension = ".cmd"
zowe = "zowe" + zowe_extension

#
# Run the command, if it fails put the output on screen
# Output is in JSON format
#
def run_command(command):
    try:
        cmd = command.replace("zowe", zowe).split(" ")
        out = json.loads(subprocess.check_output(cmd))
    except Exception as e:
        print("Error executing command:" ," ".join(cmd), "\nOutput is below: \n")
        print(json.loads(e.output.decode("utf-8")))
        exit(1)
    return out

#
# submit the job, check for return code
#
def submit_job(ds_name, output_dir, maxrc):
    command = "zowe jobs submit data-set {} -d {} --rfj".format(ds_name, output_dir)
    zowe_output = run_command(command)
    retcode = zowe_output['data']['retcode']
    if int(retcode.split(" ")[1]) > maxrc:
        print("{} exceeded max return code {}".format(ds_name, maxrc))
        exit(1)
    print(ds_name, retcode)

#
# Takes a list of jobs to run and submits them
#
def submit_multiple_jobs(jobs):
    if len(jobs):
        for job in jobs:
            submit_job(job, args.output, args.maxrc)

#
# This gets a list of the dataset members and creates a list
# output looks like "mcqth01.jcl.ex(member)", "mcqth01.test.jcl(member)"
# This can then be passed to submit multiple jobs
#
def get_dataset_members(dataset):
    out = run_command("zowe files list am {} --rfj".format(dataset))
    members = []
    for member in out["data"]["apiResponse"]["items"]:
        members.append("{}({})".format(dataset,member['member']))
    return members

#
# Get the arguments for the command
#
parser = argparse.ArgumentParser()
parser.add_argument("--ds", "--dataset", help="Dataset for jobs", required=True, dest='dataset')
parser.add_argument("-o","--output", help="Output directory", default="commands")
parser.add_argument("-m", "--maxrc", help="Max return code for jobs", default=0, type=int)
args = parser.parse_args()

# 
# Get the dataset with member and run them
#
jobs_to_run = get_dataset_members(args.dataset)
submit_multiple_jobs(jobs_to_run)
