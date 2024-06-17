python3 userDataRate.py > curr_ips.txt
cat curr_ips.txt >> exp_ip_log.txt
#scp curr_ips.txt anath@snl-server-2.cs.ucsb.edu:~/
cat curr_ips.txt | grep -o "'[0-9.]*'" | xargs echo
