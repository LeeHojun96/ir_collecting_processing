# 설명 : 여러 명령어 실행 후 결과를 파일로 저장

# from apachelogs import LogParser
import subprocess
import re
import getopt
import sys
import os

 

def isIP(Ip):
    # 파라미터가 IP 포맷인지 확인
    regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    if(re.search(regex, Ip)):
        return True
    else:
        return False
        
def str2lines(string,connector):
    # string을 2D array로 변환 : \n로 split 후 connector로 split
    returnL = []
    lines = string.split('\n') 
    for line in lines : 
        if connector :
            parsed = line.split(connector)
        else : 
            parsed = line.split()
        returnL.append(parsed)
    return returnL

def output2Lines(command, split = '\n') : 
    # 명령어의 결과물을 UTF-8로 디코딩하여 string으로 반환
    errorcode = 0
    try : 
        output = subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL).decode('UTF-8')
    except subprocess.CalledProcessError as error:
        errorcode = error.returncode
    if errorcode :
        return None
    else : 
        return output.split(split) 

def str2file(output, filename) : 
    with open("{}".format(filename), "w") as f : 
        f.write(str(output))

def list2str(list,connector) :
    return (connector.join(map(str, list)))

def getFileContent(filepath) : 
    # 파일의 내용을 읽어 반환한다.
    output = subprocess.check_output("cat {}".format(filepath), shell=True).decode('UTF-8')
    if "No such file or directory" in output :
        return None
    else : 
        return output

def ifconfigWithCol(output) : 
    # ifconfig 결과값에서 columnL에 있는 column 명의 것들만 골라 dictionary 형태로 반환
    returnDict = {}
    lines = output.split('\n') 
    adapter = ""
    for line in lines : 
        if not line :
            continue
        else :  
            parsed = line.split()
            if not line.startswith(' ') : 
                adapter = parsed[0]
                returnDict[adapter]= {}
            for i, key in enumerate(parsed) :
                if key == "inet" or key == "ether" or key == "HWaddr":
                    returnDict[adapter][key] = parsed[i+1]
    return returnDict

def AIAULineList_Netstat(output) : 
    # netstat에서 Active Internet, Active UNIX 분할해서 각각 list로 리턴
    netstatLine = output.split('\n') 
    aiStart = 0 
    aiEnd = 0
    auStart = 0
    for i, line in enumerate(netstatLine) : 
        if 'Active Internet' in line : 
            aiStart = i+2
        if 'Active UNIX' in line : 
            aiEnd = i-1
            auStart = i
    return netstatLine[aiStart:aiEnd+1], netstatLine[auStart:]

def selectColInLineList(linelist, columnL, connector = None) : 
    # 2차원 배열에서 column에 해당하는 원소들만 남겨 반환한다.
    # columnL에 있는 숫자 번째의 원소들만 남김
    returnList = []
    for line in linelist : 
        elementlist = [] 
        parsed = line.split(connector)
        for i in columnL : 
            if i-1 >= len(parsed) : 
                elementlist.append('-')
            else :
                elementlist.append(parsed[i-1])
        returnList.append(elementlist)
    return returnList

def twoDArr2file(linelist, filename, connector = '\t', column = None) : 
    # 2차원 array를 파일로 예쁘게 저장
    # 각 라인으로 저장하며 라인 내에서 구분자는 \t가 기본값이다.
    with open("{}".format(filename), "w") as f : 
        if column : 
            f.write(list2str(column, connector))
        else : 
            pass
    with open("{}".format(filename), "a") as f : 
        for line in linelist : 
            f.write(list2str(line, connector) + '\n')

def joinColumns(parsed, columnIndexList, connector = " ") :
    # column들끼리 connector로 연결시켜 하나의 string으로 만들어 반환
    if len(columnIndexList) == 0 : 
        return None
    returnStr = str(columnIndexList[0])
    if len(columnIndexList) == 1 :
        return returnStr
    for i in columnIndexList[1:] :
        returnStr += (connector + str(parsed[i]))
    return returnStr


def findFile(fileName, startDir = '/') :
    # startDir 부터 fileName에 해당하는 파일을 찾아 경로를 반환
    result = output2Lines("find {} -name {}".format(startDir, fileName))
    if not result : 
        return None 
    if '' in result : 
        while not '' in result :
            result.remove('')
    return result

################################################################################################
####################################        collect         ####################################
################################################################################################
################################################################################################
# 1. 시스템 정보

def uname(dirName) : 
    # uname 명령어 실행 결과 수집
    try: 
        subprocess.call("uname -a > ./{}/uname".format(dirName), shell=True) # 커널 정보
    except : 
        print("uname fail")

def timedatectl(dirName) :
    # timedatectl 명령어 실행 결과 수집
    try: 
        subprocess.call("timedatectl > ./{}/timedatectl".format(dirName), shell=True) # timezone 정보
    except : 
        print("timedatectl fail")


################################################################################################
# 2. 네트워크 정보

def ifconfig(dirName) : 
    # ifconfig 명령어 결과물 수집 후 필요한 column 선택하여 수집
    try : 
        subprocess.call("ifconfig -a > ./{}/ifconfig".format(dirName), shell=True) # 커널 정보 
        ifconfig = (subprocess.check_output("ifconfig -a", shell=True)).decode('UTF-8')
        ifconfigDict = ifconfigWithCol(ifconfig) # 필요 column 선택
        str2file(str(ifconfigDict), "./{}/ifconfig_parsed".format(dirName))
    except : 
        print("ifconfig fail")


def netstat(dirName) :
    # netstat 명령어 결과물 수집
    try :  
        netstat = subprocess.check_output("netstat -nap", shell=True).decode('UTF-8')
        # 칼럼 선택
        activeInternetLineList, activeUnixLineList = AIAULineList_Netstat(netstat)
        columnL = [4,5,6,7] # local address & port, state, PID/Program Name
        activeInternetLineList = selectColInLineList(activeInternetLineList, columnL)
        columnL = [7,8] 
        activeUnixLineList = selectColInLineList(activeUnixLineList, columnL)
        # 파일로 저장
        twoDArr2file(activeInternetLineList, "./{}/netstat_activeInternet".format(dirName))
        twoDArr2file(activeUnixLineList, "./{}/netstat_activeUNIX".format(dirName))
    except : 
        print("netstat fail")


def sshConfig(dirName) : 
    # ssh 설정 파일 수집
    try : 
        lines = output2Lines("cat /etc/ssh/ssh_config")
        if not lines : 
            return -1
        saveStr = ""
        for line in lines : 
            if not line : 
                continue
            if line.startswith("#") or line.startswith("Include") or line.startswith('Host '):
                continue
            saveStr += (line + '\n')
        str2file(saveStr, './{}/ssh_config'.format(dirName))
    except : 
        print("ssh config fail")

def PAMconfig(dirName) : 
    # 리눅스에서 보안 설정과 관련된 PAM 디렉터리 수집
    # 디렉터리 생성
    try : 
        subprocess.call("mkdir -p ./{}/pam".format(dirName), shell=True)
    except : 
        pass
    # 파일들 리스팅 
    try : 
        lines = output2Lines("ls /etc/pam.d", split=None)
        if not lines : 
            return -1
        for filename in lines : 
            saveStr = ""
            filepath = '/etc/pam.d/' + filename 
            content = getFileContent(filepath)
            if not content :
                continue 
            contentLines = content.split('\n')
            for line in contentLines : 
                if line.startswith("#") or line.startswith("@include"):
                    continue
                saveStr += (line + '\n')
            str2file(saveStr, './{}/pam/'.format(dirName)+filename)
    except : 
        print("PAM config fail")


def ftp(dirName) : 
    # ftp 관련 정보 수집, 설정 파일과 로그 수집 후 필요 column 선택하여 수집
    try : 
        subprocess.call("cp /var/log/xferlog > ./{}/ftp_xferlog".format(dirName), shell=True)

        lines = output2Lines("cat /etc/inetd.conf")
        if not lines : 
            return -1
        saveLines = []
        for line in lines :
            if not line : 
                continue
            parsed = line.split()
            columnL = [0,1,2,3,4]
            time = joinColumns(parsed, columnL)
            host = parsed[6]
            fileName = parsed[8]
            direction = parsed[11]
            accessMode = parsed[12]
            username = parsed[13]
            newLine = [time,host,fileName,direction,accessMode,username] # 필요 column 
            saveLines.append(newLine)
        twoDArr2file(saveLines,"./{}/ftp_xferlog_parsed".format(dirName))
        return 1
    except : 
        print("ftp fail")
        return -2

################################################################################################
# 3. 프로세스 정보

def ps(dirName) : 
    # pstree 명령어 결과물 수집 후 필요한 column 선택하여 수집
    try : 
        subprocess.call("ps -auxf > ./{}/ps".format(dirName), shell=True)

        lines = output2Lines("ps -auxf")
        if not lines : 
            return -1
        saveLines = []
        for line in lines : 
            if line : 
                parsed = line.split(sep=None,maxsplit=10)
                newLine = [parsed[0], parsed[1], parsed[-1]] # 필요한 column 
                saveLines.append(newLine)
        twoDArr2file(saveLines,"./{}/ps_parsed".format(dirName))
        return 1
    except : 
        print("ps fail")
        return -2

def pstree(dirName) : 
    # pstree 명령어 결과물 수집
    try : 
        subprocess.call("pstree -ap > ./{}/pstree".format(dirName), shell=True)
        return 1
    except : 
        print("pstree fail")
        return -2

def lsof(dirName) : 
    # lsof 명령어 결과물 수집 후 필요 column만 선택해 수집
    try : 
        subprocess.call("lsof > ./{}/lsof".format(dirName), shell=True)
        lines = output2Lines("lsof")
        if not lines : 
            return -1
        pwlines = output2Lines("cat /etc/passwd")
        if not pwlines : 
            pass
        columnL = [1]  # 게정명, uid, 홈디렉터리, 로그인쉘
        accountLinelist = selectColInLineList(lines, columnL, connector = ":")
        rebuildLines = []
        for line in lines : 
            if not line : 
                continue
            parsed = line.split()
            # command, pid, user, name
            command = parsed[0]
            pid = parsed[1]
            user = ""
            for col in parsed  : 
                for account in accountLinelist:
                    if account[0] == col :
                        user = col
                        break
                if user : 
                    break
            name = parsed[-1]
            rebuild = [command, pid, user, name]
            rebuildLines.append(rebuild) 
        twoDArr2file(rebuildLines, "./{}/lsof_parsed".format(dirName))
        return 1
    except : 
        print("lsof fail")
        return -2


def lsmod(dirName) : 
    # lsmod 명령어 결과물 수집
    try : 
        subprocess.call("lsmod > ./{}/lsmod".format(dirName), shell=True)
        return 1 
    except : 
        print("lsmod fail")
        return -2


################################################################################################
# 4. 데몬 정보

def inetd(dirName) : 
    # 데몬 관련 설정파일 수집
    try : 
        lines = output2Lines("cat /etc/inetd.conf")
        if not lines : 
            return -1
        saveLines = []
        for line in lines :
            if not line : 
                continue
            if line.startswith('#'): 
                continue
            parsed = line.split()
            command = joinColumns(parsed,range(7,len(parsed)))
            newline = [parsed[0],parsed[4],parsed[5],command]
            saveLines.append(newline)
        twoDArr2file(saveLines,"./{}/inetd".format(dirName))
        return 1
    except :
        print("inetd fail")
        return -2

def xinetd(dirName) : 
    # 데몬 관련 디렉터리인 xinetd 수집
    try : 
        subprocess.call("mkdir -p ./{}/xinetd".format(dirName), shell=True)
        lines = output2Lines("ls /etc/xinetd/", split = None)
        if not lines : 
            return -1
        for filename in lines : 
            flag = 0
            saveLines = []
            filepath = '/etc/xinetd/' + filename 
            content = getFileContent(filepath)
            if not content :
                continue 
            contentLines = content.split('\n')
            for line in contentLines : 
                if line.startswith("#") or line.startswith("@include") or line.startswith('{') or line.startswith('}'):
                    continue
                else :
                    parsed = line.split('=')
                    newline = list(map(lambda x:x.strip(),parsed))
                    saveLines.append(newline)
            twoDArr2file(saveLines,'./{}/xinetd/{}'.format(dirName, filename))
        return 1
    except : 
        print("xinetd fail")
        return -2

def service(dirName) : 
    # service --status-all 명령어 결과물 수집
    try : 
        lines = output2Lines("service --status-all")
        if not lines : 
            return -1
        saveLines = []
        for line in lines : 
            if not line : 
                continue
            parsed = line.split("]",1)
            parsed = list(map(lambda x:x.strip(),parsed))
            if "+" in parsed[0] :
                flag = "+"
            elif "-" in parsed[0]:
                flag = "-"
            newline = [flag,parsed[1]]
            saveLines.append(newline)
        twoDArr2file(saveLines,'./{}/service'.format(dirName))
        return 1
    except : 
        print("service fail")
        return -2

def crontab(dirName) : 
    # crontab 파일 수집
    try : 
        lines = output2Lines("cat /etc/crontab")
        if not lines : 
            return -1
        saveLines = []
        for line in lines : 
            if not line : 
                continue
            if line.startswith("#") or line.startswith("SHELL=") or line.startswith("PATH=") or (not line) : 
                continue
            parsed = line.split()
            user = parsed[5]
            command = joinColumns(parsed, range(6,len(parsed)))
            newline = [user,command]
            saveLines.append(newline)
        twoDArr2file(saveLines,'./{}/crontab'.format(dirName))
    except : 
        print("crontab fail")
        return -2


################################################################################################
# 5. 디스크 정보

def df(dirName) :
    # df -T 명령어 결과물 수집 후 필요 Column 선택하여 수집
    try : 
        lines = output2Lines("df -T")
        if not lines : 
            return -1
        saveLines = []
        flag = 0
        for i,line in enumerate(lines) : 
            if not line: 
                continue
            if line.startswith("Filesystem") : 
                flag = 1
            if flag : 
                parsed = line.split()
                if len(parsed) < 2 : 
                    continue
                newline = [parsed[0],parsed[1], parsed[6]] # 필요 column : filesystem(1), type(2), Mounted on(7)
            saveLines.append(newline)
        twoDArr2file(saveLines, "./{}/df".format(dirName))
    except : 
        print("df fail")
        return


################################################################################################
# 6. 계정 정보

def passwd(dirName) :
    # passwd 파일 전체 수집 후 필요 column만 추출하여 수집 
    try : 
        subprocess.call("cp /etc/passwd ./{}/passwd".format(dirName), shell=True)
        lines = output2Lines("cat /etc/passwd")
        if not lines : 
            return -1
        columnL = [1, 3, 6, 7]  # 게정명, uid, 홈디렉터리, 로그인쉘
        passwdlinelist = selectColInLineList(lines, columnL, connector = ":")
        saveLines = []
        for line in passwdlinelist : 
            if "/bin/bash" in line[3] : 
                saveLines.append(line)
        twoDArr2file(saveLines, './{}/passwd_processed'.format(dirName))
        return 1
    except : 
        print("passwd fail")
        return -2

def shadow(dirName) : 
    # shadow파일에서 필요한 columm만 수집
    try : 
        lines = output2Lines("cat /etc/shadow")
        if not lines : 
            return -1
        columnL = [1] # 게정명, uid, 홈디렉터리, 로그인쉘
        shadowlinelist = selectColInLineList(lines, columnL, connector = ":")
        twoDArr2file(shadowlinelist, './{}/shadow'.format(dirName))
        return 1
    except : 
        return -2

def bashHistory(dirName) :
    # passwd 파일을 읽어 홈디렉터리 내 bash_history를 백업
    try : 
        subprocess.call("mkdir -p ./{}/bashHistory".format(dirName), shell=True)
        lines = output2Lines("cat /etc/passwd")
        if not lines : 
            return -1
        for line in lines : 
            if not line : 
                continue
            parsed = line.split(":") 
            if parsed[-1] == "/bin/bash" :
                subprocess.call("cat {}/.bash_history > ./{}/bashHistory/{}".format(parsed[-2], dirName, parsed[0]), shell=True) # 홈 디렉터리
        return 1
    except : 
        print("bashHistory fail")
        return -2

def findAccessedFilesFromHistory(history) : 
    # bash_history 또는 history에서 접근했던 파일의 full path를 찾는다.
    accessedFileFullPathes = []
    cmds = history.split("\n")
    pwd = "/"
    for cmd in cmds : 
        if cmd.startswith("cd") : 
            dir = cmd.split()[1]
            if dir.startswith("/") : 
                pwd = dir
            else : 
                pwd += "/{}".format(dir)

        if cmd.startswith("cat") or cmd.startswith("vi") :
            parsed = cmd.split()
            if len(parsed) > 1 :
                filePath = parsed[1] 
                if not filePath.startswith("/") :
                    if pwd.endswith("/") : 
                        filePath = pwd + filePath
                    else : 
                        filePath = pwd + "/" + filePath
                accessedFileFullPathes.append(filePath)
    return accessedFileFullPathes

def saveAccessedFilesFromHistory(saveDirName, history, prefix = "") : 
    # bash_history 및 history에서 접근했던 파일들 수집
    accessedFileFullPathes = findAccessedFilesFromHistory(history)
    for fileFullPath in accessedFileFullPathes : 
        if "/" in fileFullPath : 
            fileN = prefix+ fileFullPath.split("/")[-1]
        else : 
            fileN = prefix + fileFullPath
        print(fileN)
        subprocess.call("cp {} {}/{}".format(fileFullPath, saveDirName, fileN), shell=True)

def accessedFile_bashHistory(dirName) : 
    # bash_history에 기록되어있는 접근했던 파일들 수집
    bhDir = "./{}/bashHistory".format(dirName)
    accounts = os.listdir(bhDir)
    for account in accounts : 
        with open(bhDir+"/"+account, 'r') as f : 
            history = f.read()
            saveAccessedFilesFromHistory("./{}/bashHistory".format(dirName), history, prefix = "bashHistory_accessed_file_") 

def accessedFile_history(dirName) : 
    # history 명령어 중 접근했던 파일들 수집
    with open("./"+dirName+"/history", 'r') as f : 
        history = f.read()
        saveAccessedFilesFromHistory("./{}".format(dirName), history, prefix = "history_accessed_") 


def history(dirName) : 
    # history 명령어 결과물 수집
    try : 
        subprocess.call("history > ./{}/history".format(dirName), shell=True) 
        return 1
    except : 
        print("history fail")
        return -2

def lastlog(dirName) :
    # lastlog 명령어 결과물 전체 수집 후 필요 column만 추출하여 수집 
    try : 
        lines = output2Lines("lastlog")
        if not lines : 
            return -1
        savelines = []
        for i, line in enumerate(lines) : 
            if not line : 
                continue
            newline = []
            if i == 0 : 
                continue
            parsed = line.split()
            # Username, From, Latest
            if "**Never logged in**" in line: 
                newline = [parsed[0], '-', "**Never logged in**"]
            else : 
                latest = joinColumns(parsed, range(3,len(parsed)))
                newline = [parsed[0], parsed[2], latest]
            savelines.append(newline) 
        twoDArr2file(savelines, "./{}/lastlog".format(dirName))
    except : 
        print("lastlog fail")
        return -2


################################################################################################
# 7. 시스템 정보 및 로그

def syslog(dirName) : 
    # syslog 수집
    try : 
        subprocess.call("cp /var/log/*syslog* ./{}/".format(dirName), shell=True) 
        return 1
    except : 
        print("syslog fail")
        return -2

def w(dirName) : 
    # w 명령어 결과물 전체 수집 후 필요 column만 추출하여 수집
    try :
        subprocess.call("w > ./{}/w".format(dirName), shell=True) 
        wlines = output2Lines("w -h")
        savelines = []
        for line in wlines : 
            if not line : 
                continue
            parsed = line.split()   # user(1), from(3), login@(4), what(8)
            if parsed[2] != ":0" or (not isIP(parsed[2])) : # from 부분이 빈칸일 때
                parsed.insert(2,'-')
            what = ' '.join(parsed[7:])
            newParsed = list(parsed[0:7])
            newParsed.append(what)
            columnL = [1,3,4,8]    # 필요 column : user(1), from(3), login@(4), what(8)
            newline = selectColInLineList(newParsed, columnL)
            savelines.append(newline)
        twoDArr2file(savelines, "./{}/w_parsed".format(dirName))
        return 1
    except : 
        print("w fail")
        return -2

def authlog(dirName) : 
    # auth.log 수집
    try :
        subprocess.call("cp /var/log/*auth* ./{}/".format(dirName), shell=True) 
        return 1
    except : 
        print("authlog fail")
        return -2

def last(dirName) : 
    # last 명령어 결과물 전체 수집 후 필요 column만 선택하여 수집
    try : 
        lastlines = output2Lines("last")
        savelines = []
        for line in lastlines :
            if not line : 
                continue
            if line.startswith('reboot') :
                continue
            parsed = line.split()
            starttimeInfo = joinColumns(parsed, range(3,7))
            endtimeInfo = joinColumns(parsed, range(7,len(parsed)))
            newline = [parsed[0], parsed[1], parsed[2], starttimeInfo, endtimeInfo] # 필요 column
            savelines.append(newline)
        twoDArr2file(savelines, "./{}/last".format(dirName))
        return 1    
    except : 
        print("last fail")
        return -2

def aptList(dirName) :
    # 직접 apt로 설치한 패키지 수집
    try : 
        subprocess.call("apt-mark showmanual > ./{}/aptList".format(dirName), shell=True) 
        return 1
    except : 
        print("aptList fail")
        return -2

def pipList(dirName) :
    # python의 pip으로 설치된 리스트들 수집
    try :   
        subprocess.call("pip list > ./{}/pipList".format(dirName), shell=True) 
        return 1
    except : 
        print("pipList fail")
        return -2

################################################################################################
# 8. 웹
#   - Apache

def findApacheWebRoot() : 
    # 아파치 서버의 웹루트를 찾는다.
    confPathesList = findFile('apache2.conf', startDir='/')
    if not confPathesList : 
        return -1

    savelines = []
    webRoot= ""
    confPath = confPathesList[0]
    # if len(confPathesList) > 1 :
    #     print(confPath)
    lines = output2Lines("cat {}".format(confPath))
    if not lines : 
        return -1
    
    for line in lines : 
        if line.startswith("<Directory /") :
            path = (line.split()[1])[:-1]
            webRoot = path
            if "/var/www" in path : 
                break 
    return webRoot

def findApacheLogRoot() : 
    # 환경변수에서 아파치 서버관련 변수 찾기
    #   - log 저장 디렉터리 경로
    # 설정 파일
    #   - 웹루트 경로
    
    logPath=''
    envvarPathesList = findFile('envvars', startDir='/')
    if not envvarPathesList : 
        return -1
    
    envvarPath = envvarPathesList[0]
    # if len(envvarPathesList) > 1 :
    #     print(envvarPath)
    lines = output2Lines("cat {}".format(envvarPath))
    if not lines : 
        return -1
    for line in lines : 
        if line.startswith("export ") and ("APACHE_LOG_DIR" in line):
            logPath = (line.split('=')[1]).split("$")[0]
    return logPath
    

def apacheLog(dirName) :
    # 아파치 서버의 로그들 수집
    # - access log
    # - error log
    try : 
        logPath = findApacheLogRoot()

        logFiles = output2Lines("ls {}".format(logPath))
        logFiles = logFiles[0].split()
        logFiles = [fileName for fileName in logFiles if "access" in fileName]
        # access log 백업
        subprocess.call("find " + logPath + " -name \"*access*\" | xargs cp -t " + dirName, shell=True)
        # error log 백업
        subprocess.call("find " + logPath + " -name \"*error*\" | xargs cp -t " + dirName, shell=True)
    except : 
        print("apache log fail")
        return -2

def apacheWebroot(dirName) : 
    # 아파치 웹루트 백업
    try : 
        webroot = findApacheWebRoot() 
        print("web root : " + webroot)
        subprocess.call("tar -zcvf {}/apache_webroot.tar.gz {}".format(dirName, webroot), shell=True) 
    except : 
        print("apache webroot fail")
        return -2

def apacheConfig(dirName) : 
    # 아파치 관련 설정파일 수집
    try : 
        confPathesList = findFile('apache2.conf', startDir='/')
        if not confPathesList : 
            return -1
        subprocess.call("cp {} ./{}/apache2.conf".format(confPathesList[0], dirName), shell=True)
    except : 
        print("apache config fail")
        return -2
        
def undeleteExt(dirName) : 
    # extundelete 설치 후 해당 명령어를 이용해 복구 가능한 디스크는 복구
    # 복구
    try : 
        os.system("apt-get install extundelete")
    except : 
        print("extundelete install fail")
        pass
    try : 
        df = subprocess.check_output("df -T", shell =True)
        lines = df.split('\n')
        subprocess.call("mkdir ./{}/RESTORED".format(dirName,i))
        #   ext 타입의 filesystem 찾기
        for i,line in enumerate(lines) : 
            words = line.split()
            if 'ext' in words[1] : 
                #   복구 명령 실행
                subprocess.call("mkdir ./{}/{}".format(dirName,i))
                fs = words[0]
                cmd = "extundelete {} --restore-all --output-dir ./{}/RESTORED/{}".format(fs,dirName,i)
                subprocess.call(cmd, shell = True)
        return 1
    except : 
        print("undeleteExt fail")
        return -2

## access.log 분석 -> /etc/apache2/apache2.conf 에 LogFormat 참조



################################################################################################
####################################        process         ####################################
################################################################################################
# 1. access log

# def getLogformat(dirPath) : 
#     try : 
#         logformats = []
#         mainLogFormat = ""
#         with open(dirPath+'/apache2.conf') as f :
#             lines = f.read()
#             linelist = lines.split("\n")
#             for line in linelist :
#                 if line.startswith("#") : 
#                     continue
#                 if line.startswith("LogFormat \"") : 
#                     logformats.append(line) 
#                     if "combined" in line : 
#                         mainLogFormat = line
#         if not mainLogFormat :
#             if not logformats : 
#                 return None
#             else : 
#                 mainLogFormat = logformats[0]
        
#         # line to logFormat
#         splitted = mainLogFormat.split("\"")
#         return list2str(splitted[1:-1], "\"")
#     except : 
#         print("getLogformat Fail : Maybe apache2.conf not exist")


# def process_accessLog(dirPath) : ## 로그 파서 이용
#     fileList = os.listdir(dirPath) 
#     alFileList = [fileN for fileN in fileList if "access.log" in fileN ]
#     # get logFormat from 'apache2.conf'
#     logformat = getLogformat(dirPath)
#     if not logformat :
#         print("no logformat in apache2.conf")
#         return -1 
#     parser = LogParser(logformat)
#     # read line by line => parse
#     for alFileN in alFileList:
#         with open(dirPath+'/'+alFileN) as f :
#             for line in f.readlines() :
#                 entry = parser.parse(line)
#                 request = entry.directives["%r"]
#                 uri = request.split()[1]
#                 uri.split("?")[1]
            
def post_accessLog(dirPath) :
    # access log에서 access.log 중 메소드가 POST며 200 OK 응답을 받은 로그의 URL을 경로를 중복 제거하여 보여줌
    try :
        fileList = os.listdir(dirPath) 
        alFileList = [fileN for fileN in fileList if "access.log" in fileN ]
        # read line by line => parse
        postURLs = []
        for alFileN in alFileList:
            with open('./'+dirPath+'/'+alFileN) as f :
                for line in f.readlines() :
                    if not line or line.startswith('\00') : 
                        continue
                    [request, rest] = line.split("\"",2)[1:]
                    url = request
                    [method, url, http ]= request.split()
                    if "?" in request : 
                        [url,parameters] = request.split()[1].split("?")
                    if method == "POST" and rest.startswith(" 200"): 
                        postURLs.append(url)
        return list(set(postURLs))
    except : 
        print("post_accessLog fail")
        return None

################################################################################################
# 2. network

def getLocalPorts(dirPath) :
    # 수집한 netstat 아웃풋(netstat_activeInternet)에서 머신에서 열려있는 port 정보를 수집한다.
    localPorts = {}
    try : 
        with open(dirPath+'/netstat_activeInternet') as f :
            lines = f.read()
            for line in lines.split("\n") :
                if not line : 
                    break
                localPort = (line.split()[0]).split(":")[-1]
                localPorts[localPort] = line
        return localPorts
    except : 
        print("getlocalPorts fail")
        return []

def isWellKnownPort(port) : 
    # hard coding of well-known ports
    port = str(port)
    wellKnowns = [1,5,7,18,20,21,22,23,25,29,37,42,43,49,53,68,69,70,79,80,103,108,109,110,115,118,119,137,139,143,150,156,161,179,190,194,197,389,396,443,444,445,458,546,3306,6010]
    wellKnowns = map(str,wellKnowns)
    if port in wellKnowns :
        return True
    else :
        return False

def checkUnknownPorts(dirPath) : 
    # Well-known port가 아닌 것을 출력
    localPortsDict = getLocalPorts(dirPath)
    lines = []
    if localPortsDict :
        for port in localPortsDict.keys() :
            if isWellKnownPort(port) : 
                continue
            else : 
                lines.append(localPortsDict[port])
            pass
    return lines

################################################################################################
# 3. 시스템 로그

def rootInAuthlog(dirName) : 
    # auth log에서 루트 권환과 관련된 로그들을 분류한다. 
    # - 조건
    #   - 실행 프로세스가 'sudo' 일 때
    #   - 실행 프로세스가 'su'이면서 원래 계정 또는 전환 대상 계정이 root일 때
    #   - 상세 메세지에 'uid=0'이 있을 때
    # try :
        returnDict = {}
        with open(dirName + '/auth.log') as f : 
            lines = f.read()
            if not lines : 
                print("empty auth.log")
                return None
            lines = lines.split("\n")
            for line in lines : 
                if not line : 
                    break 
                parsed = line.split(sep=None, maxsplit=5)
                proc = parsed[4]
                detail = parsed[5]
                if proc.startswith("sudo") or (proc.startswith("su") and "root" in detail) :
                    if not proc in returnDict.keys() :
                        returnDict[proc] = [line]
                    else : 
                        returnDict[proc].append(line) 
                elif ("uid=0" in detail) : 
                    if not "uid=0" in returnDict.keys() :
                        returnDict["uid=0"] = [line]
                    else : 
                        returnDict["uid=0"].append(line) 
        return returnDict

    # except : 
    #     print("root action in auth.log analysis failed")
        
################################################################################################
# 4. 설정 파일 점검


def permitRootFromSsh(dirName) : 
    # /etc/ssh/sshd_config 파일 내 "PermitRootLogin No"로 설정되어 root 접속을 막아놨는지 확인한다.
    try :
        with open(dirName + '/ssh_config') as f : 
            lines = f.read()
            if "PermitRootLogin No" in lines : 
                return False
            else : 
                return True
    except : 
        print("permitRootFromSsh failed")
        return None

def permitRootFromTelnet(dirName) : 
    # /etc/pam.d/login 파일 내 "auth required /lib/security/pam_securetty.so"로 설정되어 root 접속을 막아놨는지 확인한다.
    try :
        with open(dirName + '/PAM/login') as f : 
            lines = f.read()
            if "auth required /lib/security/pam_securetty.so" in lines : 
                return False
            else : 
                return True
    except : 
        print("permitRootFromTelnet failed")

def remoteRootAccess(dirName) : 
    # Telnet과 SSH 연결 시 root로 접근 가능하지를 점검한다.
    try : 
        remoteRootPermit={}
        remoteRootPermit["telnet"] = permitRootFromTelnet(dirName)
        remoteRootPermit["ssh"] = permitRootFromSsh(dirName)
        return remoteRootPermit
    except : 
        print("permit remote root access analysis Failed")
        return None

################################################################################################
# 5. 계정 정보 
def bashAccounts(dirName) : 
    with open(dirName + '/passwd_processed') as f : 
        return f.read()

def passwd0UidCheck(dirName) : 
    # passwd에 UID=0인 계정이 있는지 확인한다.
    try : 
        with open(dirName + '/passwd_processed') as f : 
            lines = f.read()
            lines = lines.split("\n")
            for line in lines : 
                if not line : 
                    continue
                parsed= line.split()
                if parsed[0] != 'root' and parsed[1] == '0' :
                    return line
            return "No 0 UID except root"
    except : 
        print("0 UID account check analysis Failed")
        return None


################################################################################################
# collect
################################################################################################

def collect(dirName) :
    # 1. OS 정보 
    uname(dirName) 
    timedatectl(dirName) 
    
    # 2. 네트워크 정보
    ifconfig(dirName)
    netstat(dirName)
    sshConfig(dirName)
    PAMconfig(dirName)
    ftp(dirName)

    # 3. 프로세스 정보
    pstree(dirName)
    ps(dirName)
    lsof(dirName)
    lsmod(dirName)

    # 4. 데몬 정보
    inetd(dirName)
    xinetd(dirName)
    service(dirName)
    crontab(dirName)

    # 5. 디스크 정보
    df(dirName)
    undeleteExt(dirName)

    # 6. 계정 정보
    passwd(dirName)
    shadow(dirName)
    bashHistory(dirName)
    history(dirName)
    lastlog(dirName)

    # 7. 시스템 정보 및 로그
    syslog(dirName)
    w(dirName)
    authlog(dirName)
    last(dirName)
    aptList(dirName)
    pipList(dirName)

    # 8. 웹
    apacheLog(dirName) 
    apacheWebroot(dirName) 
    apacheConfig(dirName)



################################################################################################
# process
################################################################################################

def process(collectDirPath, processDirName) : 
    # 분석 후 결과를 processDirName 디렉터리에 저장
    # 네트워크
    result = checkUnknownPorts(collectDirPath)
    if result :
        for i in result : 
            print(i)
    
    # 시스템 로그
    result = rootInAuthlog(collectDirPath) 
    if result : 
        with open(processDirName+"/rootInAuthlog", "w") as f :
            f.write(str(result))    
    # 웹 
    # - access log 
    result = post_accessLog(collectDirPath)
    if result : 
        with open(processDirName+"/post_accessLog", "w") as f :
            f.write(str(result))  
    # - syslog  

    # 원격 Root 접속 허용 여부
    result = remoteRootAccess(collectDirPath)
    if result : 
        with open(processDirName+"/permitRemoteRootAccess", "w") as f :
            f.write(str(result))     
    # 원격 Root 접속 허용 여부
    result = passwd0UidCheck(collectDirPath)
    if result : 
        with open(processDirName+"/passwd0UidCheck", "w") as f :
            f.write(str(result))    
    
    pass



def makeDir(dirName) : 
    # 결과 수집용 폴더 생성
    subprocess.call("mkdir -p {}".format(dirName), shell=True)

def main() : 
    opts,args = getopt.getopt(sys.argv[1:],"cp:")
    if not opts : 
        print('''
            ir_collector.py -c                  => collect evidences
            ir_collector.py -p <evidence_path>  => process the evidences
            ''')

    for opt,arg in opts:
        if (opt == "-c"):
            dirName = "collection_ir"
            makeDir(dirName)
            collect(dirName)
            try : 
                subprocess.call("tar -zcvf collection_ir.tar.gz collection_ir",shell=True)
            except : 
                print("tar collection_ir fail... => Manually tar")

        elif (opt == "-p"):
            dirPath = arg
            dirName = "analysisResult_ir"
            makeDir(dirName)
            process(dirPath, dirName)

        else : 
            print('''
            ir_collector.py -c                  => collect evidences
            ir_collector.py -p <evidence_path>  => process the evidences
            ''')

if __name__ == '__main__' : 
    main()

