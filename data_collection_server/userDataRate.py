import subprocess
import pandas as pd
from multiprocessing import Pool
import os
import datetime
import json
import time

def ConcatUserBahviourFiles(inputDir, outputDir):
    captureStartTime = "2022-05-12 8:15:00 PM"
    captureStartTime= pd.to_datetime(captureStartTime)

    captureDuration = 15 * 60 # in seconds
    # read all files in the directory and put them in a list
    # outputDir = "/mnt/md0/jaber/userDatarate/"
    # InputDir = "/mnt/md0/jaber/groupedUserBehavior/"
    cnt = 0
    argList = []
    dfs = []
    for root, dirs, files in os.walk(inputDir):
        print(root)
        for file in files:
            if file.endswith(".csv"):
                user = pd.read_csv(os.path.join(root, file))
                # add columns of user ip to the dataframes
                user['UserIP'] = file[:-4]
                dfs.append(user)
                cnt +=1
                print(cnt)

        dataset = pd.concat(dfs,ignore_index=True)
    # save dataset to a file
    dataset.to_csv(outputDir + "concatenatedUserBehaviour.csv", index=False)

def findRequiredUsers(userBehaviour, captureDuration, FWDdatarate, BWDdatarate, numberOfusers, accuracy_level = 0.1 , minRate, maxRate):
    #TODO:  Should I do it for each direction or both direction together?
    # Caputre duration in seconds
    # datarate in kB/s
    # totalRequiredFWDBytes = FWDdatarate * captureDuration
    # totalRequiredBWDBytes = BWDdatarate * captureDuration
    totalRequiredBytes = (FWDdatarate  + BWDdatarate) * captureDuration
    minRate *= captureDuration
    maxRate *= captureDuration
    df = pd.read_csv(userBehaviour)
    totalCurrentBytes = 0
    cnt = 0
    selectedUsers = []
    while cnt < numberOfusers:
        flowBytes = 0
        while flowBytes == 0 or flowBytes < minRate or flowBytes > maxRate:
            row = df.sample(n=1).iloc[0]
            flowBytes = row['totalFwdBytes'] + row['totalBwdBytes']

        print(flowBytes)
        if  abs((totalCurrentBytes + flowBytes) ) <= totalRequiredBytes* (1+accuracy_level):
            print(f'{flowBytes} bytes for user {row["UserIP"]}')
            print(f"Total current bytes {totalCurrentBytes}")
            selectedUsers.append(row['UserIP'])
            totalCurrentBytes += flowBytes
            cnt+=1

    #df = df.sort_values(by=['totalFwdBytes'], ascending=False)
    #x = df['totalFwdBytes'].head(10000)
    #y = df['UserIP'].head(1)
    #print(f'{x}   {y}')
    # head file.csv | column -s, -t | less -#2 -N -S
    # if the maxFwdPacketLen is greater than 200, then print UserIP
    # print(df.loc[df['maxFwdPacketLen'] > 200, 'UserIP'])


def cicStatistics(inputDir,outputfile):

    cnt = 0
    argList = []
    dfs = []
    for root, dirs, files in os.walk(inputDir):
        print(root)
        sum = 0
        for file in files:
            if file.endswith(".csv"):

                flow = pd.read_csv(os.path.join(root, file))
                # val = flow["Total Length of Fwd Packet"].values
                # sum += val
                if flow['Bwd Packet Length Max'].values > 200:
                    print(flow['Bwd Packet Length Max'].values)
                    print(f'{file}')
                    val = flow["Total Length of Bwd Packet"].values
                    sum += val
                #print(flow['Fwd Packet Length Mean'])

                # add columns of user ip to the dataframes
            # user['UserIP'] = file[:-4]
            # dfs.append(user)
            # cnt +=1
            # print(cnt)
    print(sum)

def findUserBasedOnThroughput(userBehaviour, datarate,captureDuration, minRate):
    df = pd.read_csv(userBehaviour)
    total_required_bytes = datarate * captureDuration
    up = total_required_bytes * 1.2
    down = total_required_bytes * 0.8
    currentRate = 0
    selected_users = []
    while currentRate < down:
        # randomly select users from dataset
        random_users = df.sample(n=1, replace=True)
        # calculate total byte count of randomly selected users
        random_total_bytes = random_users['totalFwdBytes'].sum() + random_users['totalBwdBytes'].sum()
        if random_total_bytes > minRate and random_total_bytes + currentRate <= up:
            currentRate += random_total_bytes
            selected_users.append(random_users['UserIP'].values[0])
    print(selected_users)
    print(len(selected_users))

if __name__ == "__main__":
    # inputDir = "/mnt/md0/jaber/groupedUserBehavior/"
    # outputDir = "/mnt/md0/jaber/userDatarate/"
    # #ConcatUserBahviourFiles(inputDir, outputDir)
    # inputFile = outputDir + "concatenatedUserBehaviour.csv"
    # findRequiredUsers(inputFile, 15*60, 1000, 800, 10, 0.1, 1000, 20000)
    # #cicStatistics("/mnt/md0/jaber/groupedCIC/169.231.109.138", "/mnt/md0/jaber/cicStatistics.csv")
