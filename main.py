# Use cdp neighbor to get switch mac address and ports with nornir_napalm napalm_get task
# from csv file match mac address to switch name and port
# then use description information from csv file to update switch port description using napalm_configure task


from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir.core.task import Result, Task
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_jinja2.plugins.tasks import template_file
import sys
import csv


nr = InitNornir(config_file="config.yaml")

def get_csv():
    # Get csv file
    with open('switches.csv', 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def get_cdp(task: Task) -> Result:
    # Get cdp neighbor
    cdp = task.run(task=napalm_get, getters=["get_cdp_neighbors"])
    return Result(host=task.host, result=cdp.result)

# If mac address from csv file matches mac address from cdp neighbor get switch port and switch name
def get_switch(task: Task, cdp: Result) -> Result:
    data = get_csv()
    for row in data:
        for key, value in cdp.result.items():
            for k, v in value.items():
                for i in v:
                    if row['mac'] == i['port_mac']:
                        row['switch'] = k
                        row['port'] = i['port']
    return Result(host=task.host, result=data)

# Use switch name and port to update switch port description
def deploy_config(task: Task, data: Result, dry_run: bool = True) -> Result:
    result_jinja2 = task.run(task=template_file, path="templates", template="config.j2", data=data.result)
    napalm_result = task.run(task=napalm_configure, dry_run=dry_run, configuration=result_jinja2.result)
    return Result(host=task.host, result=f"{napalm_result.result}")

# show diff
result = nr.run(task=get_cdp)
result = nr.run(task=get_switch, cdp=result)
result = nr.run(task=deploy_config, data=result, dry_run=True)
print_result(result)

print("Continue: Y/n")
if "n" in input().lower():
    sys.exit(0)

# push change
result = nr.run(task=deploy_config, data=result, dry_run=False)
print_result(result)

