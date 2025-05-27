# Скрипт для мониторинга схд-контроллеров при помощи hp smart storage administrator
# discover controllers
# status controller
import subprocess
import re
import json
import sys

action_type = sys.argv[1]
action_key = sys.argv[2]

ssacli_cmd = r'C:\Program Files\Smart Storage Administrator\ssacli\bin\ssacli.exe'


# возвращает список контроллеров
def get_controllers():
    ssacli = subprocess.Popen([ssacli_cmd, 'ctrl', 'all', 'show'], shell=False, stdout=subprocess.PIPE, stderr=None, stdin=None)
    out = ssacli.communicate()[0].splitlines()
    exit_code = ssacli.returncode

    if exit_code != 0:
        print("Error %s", exit_code)
        return

    ctrls = []
    for line in out:
        # print(line.decode('utf-8'))
        tokens = re.split(r' +\(sn: ', line.decode('utf-8'))
        if tokens[0]:
            ctrl = {'{#CT_NAME}': tokens[0], '{#CT_SERIAL}': tokens[1][:-1].rstrip()}
            ctrls.append(ctrl)
    # res = json.dumps(ctrls)
    return ctrls


# возвращает статус контроллера с указанным номером
def get_controller_status(ct_serial):
    ssacli = subprocess.Popen([ssacli_cmd, 'ctrl', 'serialnumber='+ct_serial, 'show', 'status'], shell=False, stdout=subprocess.PIPE, stderr=None, stdin=None)
    out = ssacli.communicate()[0].splitlines()
    exit_code = ssacli.returncode

    if exit_code != 0:
        print("Error %s", exit_code)
        return

    res_status = {}
    for bline in out:
        line = (bline.decode('utf-8')).lower()
        if 'status' in line:
            line = line.replace('/', '')
            tokens = re.split(r' status: ', line)
            res_status[tokens[0].strip()] = tokens[1].strip()
    print(json.dumps(res_status))


# возвращает список физических дисков
def get_pds():
    pds = []
    for ctrl in get_controllers():
        ssacli = subprocess.Popen([ssacli_cmd, 'ctrl', 'serialnumber='+ctrl['{#CT_SERIAL}'], 'pd', 'all', 'show', 'status'], shell=False, stdout=subprocess.PIPE, stderr=None, stdin=None)
        out = ssacli.communicate()[0].splitlines()
        exit_code = ssacli.returncode

        if exit_code != 0:
            print("Error %s", exit_code)
            return

        for line in out:
            l = line.decode('utf-8')
            match = re.search(r'\((.*?)\)', l)
            if match:
                extracted_value = (match.group(1)).replace(', spare', '')
                # , is special character
                extracted_value = extracted_value.replace(',', '')
                pdstatus = re.split(r'\): ', l)[1]
                #pd = {'{#PD_NAME}': extracted_value, '{#PD_STATUS}': pdstatus}
                pd = {'pd_name': extracted_value, 'pd_status': pdstatus}
                pds.append(pd)
    return pds


# возвращает список логических дисков и их статус
def get_lds():
    lds = []
    for ctrl in get_controllers():
        ssacli = subprocess.Popen([ssacli_cmd, 'ctrl', 'serialnumber='+ctrl['{#CT_SERIAL}'], 'ld', 'all', 'show', 'status'], shell=False, stdout=subprocess.PIPE, stderr=None, stdin=None)
        out = ssacli.communicate()[0].splitlines()
        exit_code = ssacli.returncode

        if exit_code != 0:
            print("Error %s", exit_code)
            return

        for line in out:
            l = line.decode('utf-8')
            tokens = re.split(r': ', l)
            if tokens[0]:
                # , is special character
                ldname = (tokens[0].replace(',', '')).strip()
                ldstatus = tokens[1].strip()
                ld = {'ld_name': ldname, 'ld_status': ldstatus}
                lds.append(ld)
    return lds


if (action_type == 'discover'):
    if (action_key == 'controllers'):
        print(json.dumps(get_controllers()))
    if (action_key == 'pds'):
        print(json.dumps(get_pds()))
    if (action_key == 'lds'):
        print(json.dumps(get_lds()))

if (action_type == 'status.controller'):
    get_controller_status(action_key)
