import os, sys
import re
import shutil
import operator
import datetime
import copy

from bs4 import BeautifulSoup

def summary(summary_html_file):
    ''' 抓取 loadrunner HTML report 中的 summary.html 主要數據, 
    資料存放的方式為巢狀 dict

    '''
    file_open = open(summary_html_file, 'r', encoding='utf-8')
    res = file_open.read()
    soup = BeautifulSoup(res, "html.parser")
    data = soup.find_all('span', {'class':'VerBl8'})

    raw_data_list = [] #用來存放 summary raw data 的 list
    title_list = [] #存放 summary transaction name 的 list
    
    #title 跟 raw data list 分開存放
    for i in range(len(data)):
        # use strip to delete /x0a 
        if data[i].get_text(strip=True) == 'HTTP_200':
            break
        else:
            if i % 9 == 0:
                title_list.append(data[i].get_text(strip=True))
            else:
                raw_data_list.append(data[i].get_text(strip=True))           
    
    #用 dict 的方式將 title list 與 raw data list 合併
    data_slice_list=[]
    for item in range(0, len(raw_data_list), 8):
        values = raw_data_list[item:item+8]
        keys = ['Minimum', 'Average', 'Maximum', 'Std. Deviation', '90 Percent', 'Pass', 'Fail', 'Stop']
        data_slice_list.append(dict(zip(keys, values)))
    
    data_list = dict(zip(title_list, data_slice_list))
    
    file_open.close()
    
    #取用數值的語法
    #print(data_list['Action_Transaction']['Average'])
    
    return data_list

def duration_time(summary_html_file):
    ''' 從 summary.html 取得 duration time, 只取到分鐘
    '''
    file_open = open(summary_html_file, 'r', encoding='utf-8')
    res = file_open.read()
    soup = BeautifulSoup(res, "html.parser")
    data = soup.find_all('td', {'headers':'LraDuration'})
    # just get duration time in minutes
    duration_time = data[0].get_text(strip=True).split()[0]
    file_open.close()
    return duration_time

def scenario_time(summary_html_file):
    ''' 從 summary.html 取得 scenario time
    '''
    file_open = open(summary_html_file, 'r', encoding='utf-8')
    res = file_open.read()
    soup = BeautifulSoup(res, "html.parser")
    data = soup.find_all('td',{'class':'header_timerange'})
    temp = data[0].string.split()
    
    scenario_time_data = []
    for i in range(len(temp)):
        if i == 1 or i == 3:
            scenario_time_data.append(temp[i])
        else:
            pass
    file_open.close()
    return scenario_time_data

def vusers(summary_html_file):
    ''' 從 summary.html 取得 virtual user 的數量 
    '''
    file_open = open(summary_html_file, 'r', encoding='utf-8')
    res = file_open.read()
    soup = BeautifulSoup(res, "html.parser")
    data = soup.find_all('td',{'headers':'LraMaximumRunningVusers'})
    vusers = data[0].string

    file_open.close()
    return vusers

def get_report_link(contents_html_file):
    ''' 從 contents html file 取得 圖片檔名(reportX.png) 與所對應的數據名稱(connections, vuser...)
    ''' 
    file_open = open(contents_html_file, 'r', encoding='utf-8')
    res = file_open.read()
    soup = BeautifulSoup(res, "html.parser")
    data = soup.find_all('a')
    
    report_index = {}
    for i in data: 
        if 'href' in str(i): 
            linkname = i.string
            linkaddr = i['href']
            #當 i 無內容是linkname为Nonetype類型。
            if 'NoneType' in str(type(linkname)):
                print(linkaddr)
            else:
                report_index.update({linkname : linkaddr})

    file_open.close()
    return report_index

def transcation_per_second(tps_html_file):
    ''' 從 transcation per second html file 取得 tps 數據
    '''
    file_open = open(tps_html_file, 'r', encoding='utf-8')
    res = file_open.read()
    soup = BeautifulSoup(res, "html.parser")
    data = soup.find_all('table',{'class':'legendTable'})
    data_num = len(data[0].text.split())
    tps = data[0].text.split()

    # 搜尋 list 中符合的 string
    matching = [s for s in tps if "Pass" in s]
    tps_data = []

    for i in range(len(matching)):
        num = tps.index(matching[i])
        for j in range(num, num+6):
            if j == num or j ==  num +2:
                if j == num +2:
                    tps_data.append(int(float(tps[j])*60))
                else:
                    tps_data.append(tps[j])
            else:
                pass
      
    file_open.close()
    return tps_data

def get_html_error(error_html_file):
    ''' 從 error html file 中取得 error 數量, analysis 有時在 summary 中不會自動產生 Error 數據
    '''
    if os.path.exists(error_html_file) == True:
        file_open = open(error_html_file, 'r', encoding='utf-8')
        res = file_open.read()
        soup = BeautifulSoup(res, "html.parser")
        data = soup.find_all(class_=re.compile("legendRow"))

        num_of_errors = 0
        for i in range(len(data)):
            a = float(data[i].text.strip().split()[-1])
            num_of_errors += a 
    
        file_open.close()
        return int(num_of_errors)
    else:
        num_of_errors = 0
        return num_of_errors

def get_time_to_first_buff(report_html):
    ''' 取得最耗時的 server time 元件與 network time 元件
    '''
    fin = open(report_html, 'r', encoding = 'utf-8')
    res = fin.read()
    soup = BeautifulSoup(res, "html.parser")
    data = soup.find_all('td')

    net_time_dict = {}
    srv_time_dict = {}
        
    for i in range(len(data)):
        if 'NoneType' in str(type(data[i].string)):
            pass
    
        elif 'Network Time' in str(data[i].string):
            net_name = data[i].string.strip().replace(' (main URL).[Network Time]', '')
            net_time = data[i+2].string.strip()
            net_time_dict.update({net_name : net_time})
    
        elif 'Server Time' in str(data[i].string):
            srv_name = data[i].string.strip().replace(' (main URL).[Server Time]', '')
            srv_time = data[i+2].string.strip()
            srv_time_dict.update({srv_name : srv_time})
        
    sorted_net_time = sorted(net_time_dict.items(), key=operator.itemgetter(1), reverse=True)
    sorted_srv_time = sorted(srv_time_dict.items(), key=operator.itemgetter(1), reverse=True)
        
    return sorted_net_time, sorted_srv_time

def get_table_dataToList(report_html_file):
    ''' 將 html report 中的 table 中的數據放入 list 裡
    '''
    file_open = open(report_html_file, 'r', encoding='utf-8')
    res = file_open.read()
    soup = BeautifulSoup(res, "html.parser")
    data = soup.find_all('table',{'class':'legendTable'})
    data_num = len(data[0].text.split())
    
    table_data = list()
    for i in range(data_num - 5, data_num):
        table_data.append(data[0].text.split()[i])
    
    return table_data

def get_dirs_list(current_work_directory):
    ''' 取得與腳本同目錄下所需取得數據的目錄名稱
    '''
    # add the name of diretories in work directory
    directories = []
    for directory in os.listdir(current_work_directory):
        if os.path.isdir(directory):
            # 進入 directory to check Report.html 是否存在
            os.chdir(directory)

            # 如果存在 Report.html 則把 dir name 加到 list 裡
            if os.path.exists('Report.htm'):
                directories.append(directory)
            else:
                pass

            os.chdir('../')
        else:
            pass
            #print('The Report.html file does not exist in ' + str(directories))

    #print(directories)
    return directories

def write_title(summary_html_file):
    ''' 在 CSV 檔案裡寫入標題列
    '''
    data_list = summary(summary_html_file)
    
    # 取出 keys 並加至 title name list 裡
    #title_name_list = []
    #for k in data_list.keys():
    #    if str(k) == 'vuser_end_Transaction':
    #        pass
    #    elif str(k) == 'vuser_init_Transaction':
    #        pass
    #    else:
    #        title_name_list.append(k)

    # 取出 keys 並加至 title name list 裡
    transcation_name_list = []
    for k in data_list.keys():
        if str(k) == 'vuser_end_Transaction':
            pass
        elif str(k) == 'vuser_init_Transaction':
            pass
        elif str(k) == 'Action_Transaction':
            pass
        else:
            transcation_name_list.append(k)


    # 以字母順序排序 title
    #title_name_list.sort(key=str.lower, reverse=False)
    transcation_name_list.sort(key=str.lower, reverse=False)
    transcation_name_list_sorted = copy.deepcopy(transcation_name_list)

    # 將 transcation 加入 'Std. Dev' & '90 Percent' 
    for i in range(len(transcation_name_list)):
        transcation_name_list.insert(3*i+1, 'Std. Dev')
        transcation_name_list.insert(3*i+2, '90 Percent')

    title_front_list = ['File Name', 'Date', 'Time', 'Vuser', 'Duration Time']
    title_behind_list = ['Pass', 'Fail', 'Passed %', 'Failed %', 'TPM', 'Error'\
                        , 'Avg. Conn', 'Max Conn', 'Throughput (MB)'\
                        , 'srv_consume_element', 'srv_consume_time', 'srv consume %'\
                        , 'net_consume_element', 'net_consume_time', 'net consume %']
    
    #title_name_list.insert(1, 'Std. Dev')
    title_name_list=['Action_Transaction', 'Std. Dev', '90 Percent']

    combind_title_name_list = title_front_list + title_name_list + title_behind_list + transcation_name_list
    #print(combind_title_name_list[-1])

    if os.path.isfile('../../output.csv') == True:
        pass
    else:
        fw = open('../../output.csv', 'a', encoding='utf-8')
        for i in range(len(combind_title_name_list)):
            if i == len(combind_title_name_list)-1:
                fw.write(combind_title_name_list[i] + '\n')
            else:
                fw.write(combind_title_name_list[i] + ',')  

    #for item in combind_title_name_list:
    #    if item == combind_title_name_list[-1]:
    #        fw.write(item + '\n')
    #    else:
    #        fw.write(item + ',')  
    
        fw.close()
    
    return title_name_list, transcation_name_list_sorted

def get_report_data(report_dir):
    ''' 取得 HTML report 數據並寫入至 CSV 檔案裡 
    '''
    # from contents.html to get link name
    report_index = get_report_link('contents.html')
    
    # 取得 virtual user    
    virtual_users = vusers('summary.html')
        
    # 取得 connections
    if report_index.get('Connections') == None:
        print(report_dir + ': No Connections html file.')
        exit()
    else:
        connection_data = get_table_dataToList(report_index.get('Connections'))
    
    connection = []
    for item in connection_data:
        connection.append(round(float(item.replace(',',''))))

    # 取得 Throughput (MB)
    if report_index.get('Throughput (MB)') == None:
        print(report_dir + ': No Throughput (MB) Report.html')
        exit()
    else:
        throughput = get_table_dataToList(report_index.get('Throughput (MB)'))

    
    # 取得 Error 
    if report_index.get('Error Statistics (by Description)') == None:
        error_count = 0
    else:
        error_count = get_html_error(report_index.get( \
                      'Error Statistics (by Description)'))

    # 取得 TPS
    tps = transcation_per_second(report_index.get('Transactions per Second'))

    # 取得 Summary 資訊(average respons time)
    # 回傳 dict 資料型態
    summary_data = summary('summary.html')

    # 取得 scenario_time
    scenario_time_data = scenario_time('summary.html')

    # 取得 durationTime
    duration_time_data = duration_time('summary.html')       
    
    # 開啟 csv 檔
    #fw = open('../../output.csv', 'a', encoding='utf=8')
    #fw.write(str(report_dir) + ',')

    #for item in scenario_time_data:
    #    fw.write(item + ',')

    #fw.write(str(virtual_users) + ',' + str(duration_time_data) + ',')

    # 取得 time to first buffer breakdown (over time) data
    net_time_data, srv_time_data = get_time_to_first_buff(report_index.get('Time to First Buffer Breakdown (Over Time)'))
    
    # 取出 summary 所需的數據
    csv_data = []

    csv_data.append(str(report_dir))

    for item in scenario_time_data:
        csv_data.append(item)

    csv_data.append(str(virtual_users))
    csv_data.append(str(duration_time_data))

    #title_name_list = write_title('summary.html')
    #title_name_list.remove('Std. Dev')

    title_name_list, transcation_name_list_sorted = write_title('summary.html')
    
    #for item in title_name_list:
    #    csv_data.append(summary_data[item]['Average'])

    for item in 'Average', 'Std. Deviation', '90 Percent':
        csv_data.append(summary_data['Action_Transaction'][item])
    
    # insert the Std. Deviation to the index 1
    #csv_data.insert(1, summary_data['Action_Transaction']['Std. Deviation'])

    # 取出 transcation pass & fail
    pass_tran = float(summary_data['Action_Transaction']['Pass'].replace(',',''))
    fail_tran = float(summary_data['Action_Transaction']['Fail'].replace(',',''))

    # 計算 transcation pass & fail
    pass_percent = round((pass_tran / (pass_tran + fail_tran)), 3)
    fail_percent = round((fail_tran / (pass_tran + fail_tran)), 3)
    
    # add pass / fail tran, pass / fail percent value to csv_data
    for item in int(pass_tran), int(fail_tran), pass_percent, fail_percent:
        csv_data.append(item)
    

    csv_data.append(tps[1])
    csv_data.append(error_count)
    
    for i in range(1, 3):
        csv_data.append(connection[i])

    #print(csv_data)

    csv_data.append(throughput[1])

    for i in range(0, 2):
        csv_data.append(srv_time_data[0][i])
        if i == 1:
            srv_consume_percent = float(srv_time_data[0][i]) / float(summary_data['Action_Transaction']['Average'])
            csv_data.append(srv_consume_percent)
    
    for i in range(0, 2):
        csv_data.append(net_time_data[0][i])
        if i == 1:
            net_consume_percent = float(net_time_data[0][i]) / float(summary_data['Action_Transaction']['Average'])
            csv_data.append(net_consume_percent)
    
    # 加入 transcation data
    #print(transcation_name_list_sorted)
    #exit()

    for Transaction in transcation_name_list_sorted:
        for item in 'Average', 'Std. Deviation', '90 Percent':
            csv_data.append(summary_data[Transaction][item])
    
    # 將取出的數據寫入 csv 檔

    fw = open('../../output.csv', 'a', encoding='utf=8')
    for i in range(len(csv_data)):
        if i == len(csv_data) - 1 :
            fw.write(str(csv_data[i]) + '\n')
        else:
            fw.write(str(csv_data[i]) + ',')

        i += 1

    fw.close()
    return

def get_graph(contents_file, data_file_name, now_time, dst_dir):
    ''' 複製並更名 reportX.png 至指定的資料夾裡 
    '''
    report_index = get_report_link(contents_file)

    if not os.path.isdir(dst_dir):
        os.mkdir(dst_dir)
    
    get_graph_name = ('Connections', 'Throughput (MB)', 'Running Vusers', 'Hits per Second')
        
    for item in get_graph_name:
        ori_file_name = report_index.get(item).replace('.html', '.png')
        
        if str(item) == 'Connections':
            dst_file_name = dst_dir + '/' + data_file_name  + '_connection.png'
            shutil.copy(ori_file_name, dst_file_name)
        elif str(item) == 'Throughput (MB)':
            dst_file_name = dst_dir + '/' + data_file_name + '_throughtput.png'
            shutil.copy(ori_file_name, dst_file_name)
        elif str(item) == 'Running Vusers':
            dst_file_name = dst_dir + '/' + data_file_name + '_vusers.png'
            shutil.copy(ori_file_name, dst_file_name)     
        else:
            dst_file_name = dst_dir + '/' + data_file_name + '_hitsPerSecond.png'
            shutil.copy(ori_file_name, dst_file_name)
    return

if __name__ == '__main__':

    dir_path = os.getcwd()
    dirs_list = get_dirs_list(dir_path)
    now_time = datetime.datetime.now().strftime("%m%d")
    dst_dir = '../../TestReport_' + str(now_time)
    
    for item in dirs_list:
        
        if os.path.isdir(item + '/Report') == True:
            os.chdir(dir_path + '/' + item + '/Report')
            
            #if not os.path.exists('../../output.csv'):
                #md.write_title('summary.html')
                        
            #md.get_report_data(item)
            #md.get_graph('contents.html', item, now_time, dst_dir)
            get_report_data(item)
            get_graph('contents.html', item, now_time, dst_dir)
            
            print(item + ': done.')
            
            os.chdir('../..')
        else:
            print(item + ': No HTML Report.')
            pass