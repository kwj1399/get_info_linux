#!/usr/bin/python
# -*- coding:utf8 -*-
__author__ = 'kwj'

import subprocess
import re
import paramiko
from time import sleep

server_user='root'
server_pw='mima'
server_info={}

def getCPU(cpu_stat):
    # 返回CPU当前的总时间片和空闲时间片信息的数据
    sys_cpu_info_t = re.findall(r'cpu .*\d',cpu_stat)
    cpu_z_str = ' '.join(sys_cpu_info_t)
    cpu_z_list = list(cpu_z_str.split())
    cpu_z_list.remove("cpu")
 
    f_line_a=[]
    for i in cpu_z_list:
        i=int(i)
        f_line_a.append(i)
    total = sum(f_line_a)
    idle = f_line_a[3]
    return total,idle

def getMEM(meminfo_r):
    # 返回内存使用信息的一个字典，取值需要 /proc/meminfo 的内容
    aa = re.sub(r' kB','',meminfo_r)
    bb = re.sub(r' +','',aa)
    cc = re.sub(r'\n',':',bb)
    dd = cc.split(":")

    meminfo_d = {}
    while len(dd)>1:
        meminfo_d[dd[0]]=dd[1]
        del dd[0:2]
    return meminfo_d

def getPING(ip):  
    time_str = []
    for i in range(10):
        p = subprocess.Popen(["ping -c 1 "+ ip], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)  
        out = p.stdout.read()  
        time = filter(lambda x:x in '1234567890.',re.search((u'time=\d+\.+\d*'),out).group())
        time_str.append(time)
        time_num = sum([float(x) for x in time_str])/10
    ip = re.search((r'\d+\.\d+\.\d+\.\d*'),out).group()	
    return time_num

if __name__=='__main__':
    host=['172.25.1.12','172.25.1.13','172.25.1.14']
    for i in host:
        #SSH远程
        ss = paramiko.SSHClient()
        ss.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ss.connect(i,22,server_user,server_pw)
        #通过两次获取CPU信息来计算CPU使用率，sleep(3)
        stdin,stdout,stderr = ss.exec_command('cat /proc/stat')
        cpu_stat = stdout.read()        
        total_a,idle_a = getCPU(cpu_stat)
        sleep(3)
        stdin,stdout,stderr = ss.exec_command('cat /proc/stat')
        cpu_stat = stdout.read() 
        total_b,idle_b = getCPU(cpu_stat)
        #获取内存信息        
        stdin,stdout,stderr = ss.exec_command('cat /proc/meminfo')
        mem_stat = stdout.read()
        ss.close()
        #计算CPU使用率，小数格式
        sys_idle = idle_b - idle_a
        sys_total = total_b - total_a
        sys_used = sys_total - sys_idle
        cpu_used = (float(sys_used)/sys_total)*100
        #计算内存使用率，小数格式
        meminfo = getMEM(mem_stat)
        mem_used_a = int(meminfo.get('MemTotal'))-int(meminfo.get('MemFree'))-int(meminfo.get('Buffers'))-int(meminfo.get('Cached'))
        mem_used = (float(mem_used_a)/int(meminfo.get('MemTotal')))*100
        #获取ping的网络延时
        nl = getPING(i)

        weight = ((cpu_used*mem_used)**0.5)*(1+nl)
        server_info_list = [cpu_used,mem_used,nl,weight]
        server_info[i] = server_info_list
            
    print server_info
    server_sorted = sorted(server_info.iteritems(),key=lambda x:x[1][3])
    server_priority = []
    for key in server_sorted:
        server_priority.append(key[0])
    print server_priority

        
