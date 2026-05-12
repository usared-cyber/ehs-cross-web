from flask import Flask, render_template
import requests
import json
from datetime import datetime, timedelta
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app = Flask(__name__)

# 配置信息
API_KEY = "5Lie3moye4j0mxQgPFoFmIt03TZSu1YO5D7057a43E1E2860aEc083b0846Bd2e8"
APP_ID = "69604d78e35647a5d28f68e6"
ENTRY_ID = "69fd956bcbcb501cb1db0dc05"

def get_jiandaoyun_data():
    """从简道云接口获取数据"""
    # 确保使用 api. 子域名
    url = "https://api.jiandaoyun.com/api/v4/app/69604d78e35647a5d28f68e6/entry/69fd956cbcb501cb1db0dc05/data"
    headers = {'Authorization': f'Bearer {API_KEY.strip()}', 'Content-Type': 'application/json;charset=utf-8'}
    try:
        response = requests.post(url, headers=headers, json={"limit": 100}, verify=False, timeout=15)
        return response.json().get('data', [])
    except: return []

@app.route('/')
def safety_cross():
    now = datetime.now()
    today_date = now.date()
    
    data_list = get_jiandaoyun_data()
    status_map = {} 
    start_date_str = "2022-09-13" 

    for item in data_list:
        # 1. 提取起始日期
        if item.get('_widget_1778226542631'):
            start_date_str = str(item['_widget_1778226542631'])[:10]
        
        # 2. 提取申报日期：针对 UTC 16:00 (北京时间 00:00) 进行加1天补偿
        raw_report = item.get('_widget_1778226542635')
        if raw_report:
            raw_str = str(raw_report)
            if "T16:00:00" in raw_str or "T15:00:00" in raw_str:
                dt_obj = datetime.strptime(raw_str[:10], '%Y-%m-%d') + timedelta(days=1)
                report_key = dt_obj.strftime('%Y-%m-%d')
            else:
                report_key = raw_str[:10]
            
            eval_text = item.get('_widget_1778226542627', '')
            if "无事故" in eval_text: status_map[report_key] = "green"
            elif "观察" in eval_text or "未遂" in eval_text: status_map[report_key] = "yellow"
            elif any(x in eval_text for x in ["急救", "LTI", "事故", "治疗"]): status_map[report_key] = "red"

    # 3. 逻辑：9点前若无昨日记录，自动补绿
    yesterday_str = (today_date - timedelta(days=1)).strftime('%Y-%m-%d')
    if now.hour < 9 and yesterday_str not in status_map:
        status_map[yesterday_str] = "green"

    # 4. 天数计算 (固定结果 1336)
    start_dt = datetime.strptime(start_date_str[:10], '%Y-%m-%d').date()
    days_diff = (today_date - start_dt).days - 1 

    calendar_days = []
    for i in range(1, 32):
        try:
            curr_obj = now.replace(day=i).date()
            date_key = curr_obj.strftime('%Y-%m-%d')
            if curr_obj > today_date: state = "future"
            elif curr_obj == today_date: state = "today-active"
            else: state = status_map.get(date_key, "green")
            calendar_days.append({"day": i, "color": state})
        except ValueError: continue

    return render_template('index.html', days=days_diff, calendar_days=calendar_days)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')


