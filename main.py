import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

def print_with_time(message):
    """带时间戳的打印"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {message}")

def login_and_get_cookie():
    """登录 SSPanel 并获取 Cookie"""
    email = os.getenv('IKUUU_EMAIL')
    password = os.getenv('IKUUU_PASSWORD')
    
    if not email or not password:
        print_with_time("❌ 错误: 请设置 IKUUU_EMAIL 和 IKUUU_PASSWORD 环境变量")
        return None
    
    print_with_time(f"🔑 正在使用账号 {email[:3]}***{email.split('@')[1]} 登录...")
    
    session = requests.Session()
    
    # 首先访问登录页面获取必要的信息
    login_page_url = "https://ikuuu.nl/auth/login"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0'
    }
    
    try:
        # 获取登录页面
        response = session.get(login_page_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找 CSRF token
        csrf_token = None
        csrf_input = soup.find('input', {'name': '_token'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
        
        # 准备登录数据
        login_data = {
            'email': email,
            'passwd': password
        }
        
        if csrf_token:
            login_data['_token'] = csrf_token
        
        # 发送登录请求
        login_url = "https://ikuuu.nl/auth/login"
        headers.update({
            'Origin': 'https://ikuuu.nl',
            'Referer': 'https://ikuuu.nl/auth/login',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        
        response = session.post(login_url, data=login_data, headers=headers)
        
        # 检查登录是否成功
        if response.status_code == 200:
            # 检查响应内容判断登录状态
            if 'user' in response.url or response.json().get('ret') == 1:
                print_with_time("✅ 登录成功")
                # 提取 Cookie
                cookies = session.cookies.get_dict()
                cookie_string = '; '.join([f"{name}={value}" for name, value in cookies.items()])
                return cookie_string
            else:
                result = response.json()
                print_with_time(f"❌ 登录失败: {result.get('msg', '未知错误')}")
                return None
        else:
            print_with_time(f"❌ 登录请求失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print_with_time(f"❌ 登录过程中发生错误: {str(e)}")
        return None

def checkin(cookie):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
        'Origin': 'https://ikuuu.nl',
        'Referer': 'https://ikuuu.nl/user',
        'Cookie': cookie
    }
    url = "https://ikuuu.nl/user/checkin"
    
    try:
        response = requests.post(url, headers=headers)
        data = response.json()
        
        if data.get('ret') == 1:
            print_with_time(f"✅ 签到成功: {data['msg']}")
            return True
        elif "已经签到" in data.get('msg', ''):
            print_with_time(f"ℹ️ 今日已签到: {data['msg']}")
            return True
        else:
            print_with_time(f"❌ 签到失败: {data['msg']}")
            return False
    except Exception as e:
        print_with_time(f"❌ 签到请求失败: {str(e)}")
        return False

def get_user_traffic(cookie):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
        'Origin': 'https://ikuuu.nl',
        'Referer': 'https://ikuuu.nl/user/code',
        'Cookie': cookie
    }
    url = "https://ikuuu.nl/user"
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找剩余流量信息
        traffic_cards = soup.find_all('div', class_='card-statistic-2')
        
        print_with_time("📊 流量使用情况:")
        print("=" * 50)
        
        for card in traffic_cards:
            header = card.find('h4')
            if header and '剩余流量' in header.text:
                # 提取剩余流量数值
                body = card.find('div', class_='card-body')
                if body:
                    remaining_traffic = re.sub(r'\s+', ' ', body.get_text(strip=True))
                    print(f"📈 剩余流量: {remaining_traffic}")
                
                # 提取今日已用流量
                stats = card.find('div', class_='card-stats-title')
                if stats:
                    today_used_text = re.sub(r'\s+', ' ', stats.get_text(strip=True))
                    # 提取冒号后的数值部分
                    match = re.search(r':\s*(.+)', today_used_text)
                    if match:
                        today_used = match.group(1).strip()
                        print(f"📊 今日已用: {today_used}")
                    else:
                        print(f"📊 今日使用情况: {today_used_text}")
        
        print("=" * 50)
        return soup
    except Exception as e:
        print_with_time(f"❌ 获取流量信息失败: {str(e)}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print_with_time("🚀 iKuuu 自动签到程序启动")
    print("=" * 60)
    
    # 登录获取 Cookie
    cookie_data = login_and_get_cookie()
    
    if not cookie_data:
        print_with_time("❌ 程序终止")
        exit(1)
    
    # 执行签到
    checkin(cookie_data)
    
    # 获取流量信息
    get_user_traffic(cookie_data)
    
    print("=" * 60)
    print_with_time("✨ 程序执行完成")
    print("=" * 60)
