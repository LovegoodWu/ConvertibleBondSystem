import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import winsound
from dotenv import load_dotenv

import requests
import time
import json

load_dotenv()  # 加载.env文件


def monitor_tickets():
    # 设置请求头
    see_match_headers = {
        "Host": "xcx-api.dasheng.top",
        "sign": "f3fe48e11692acacff19193762544254",
        "accessKey": "Bearer 3578fb911e8845918471f2108fddd558",
        "content-type": "application/json",
        "Authorization": "eyJhbGciOiJIUzUxMiJ9.eyJ3ZWJfYXBwX2xvZ2luX3VzZXJfa2V5IjoiNDdlYWNjYTcwOWQ4YWFiNDMxNzYxY2JkZjEzZWUzOTYifQ.e5p-83MFYPN8qxEHtCsnzHdUQICabtqo8BuWjQrAl-XJuO9HPodV4BJq4LS18miR9a9kJgB7h4L-k_vFKGGTtw",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.56(0x18003836) NetType/WIFI Language/zh_CN",
        "Referer": "https://servicewechat.com/wxfabc7ab137658e55/165/page-frame.html"
    }

    # 设置请求数据
    see_match_data = {
        "id": "1897522522790432769"
    }

    # 设置请求URL
    see_match_url = "https://xcx-api.dasheng.top/api/ticket/v1/app/search/ticket/show/detailInfo/noSeat"

    # 请求URL
    planet_url = "https://m.piaoxingqiu.com/cyy_gatewayapi/show/pub/v5/show/67c53853d18e67000126d064/session/67c538d503193c00018e0d6e/seat_plans?lang=zh&src=weixin_mini&merchantId=6267a80eed218542786f1494&ver=4.27.1&appId=wxad60dd8123a62329&source=FROM_QUICK_ORDER"

    # 请求头
    planet_headers = {
        "Host": "m.piaoxingqiu.com",
        "terminal-src": "WEIXIN_MINI",
        "content-type": "application/json",
        "src": "weixin_mini",
        "ver": "4.27.1",
        "access-token": "eyJ0eXAiOiJKV1QiLCJjdHkiOiJKV1QiLCJ6aXAiOiJERUYiLCJhbGciOiJSUzUxMiJ9.eNp8UUtzgjAQ_i85e4CQB3izWCtTHayKoycmkGXKjAKSYLWO_70JWqenHrPfczdXVItOf0ZVUaPhFYmmiSQaoq-zkMyR0nexJxj2cIAGqKvKuurhOtmumTpP5CmJju_BW8bLcbr5KPOTowyxbuDBiyZRTCO8yY_xOVTb7cbtmhUXcqUUuhlHBe1vdFZ-h7UEo5pMZ-nc2Kgue3kOGWZc-A6AxK5PCeY-K1wSEMMzymW9t6SXZPe6NJODzhNrbTvQ3CMUsgJI5lAhRO5AximBu_BJY9gvWOYE4BUQeMwlDBMiJbM1DS9uoBW6_o_LsbHUl8YUcU0FaPNPUen7elW33w_QCVplTtjjjWh1qfsXYkYI56ZsYV0erJwTl3KKuUMdNkB5C0L_gYjv-w9IXZSGw-NE4ShKd1EazuJknPanSBfJMpyOVq_pYjZaT-Ll_J70N8L4m54V7O1q9572Wyph4-z79gMAAP__.T8AA42NCGJw9I6RQvIqaoeUk2Dj_XuqH9bY38yGM7q6WZ4Y57-76MYH0JmgrMQlgPkVKk4pHUWzrqc8W1cl4ROFL7QdmDPbPGFk7ST5zyhaQ4o9ahYojsrLEJ6YiM4ApHG13ZqgBSHbknyILruzIJ-OgDwdsJssOaN6xhxUBZ5M",
        # 替换为实际的access-token
        "merchant-id": "6267a80eed218542786f1494",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.56(0x18003836) NetType/WIFI Language/zh_CN",
        "Referer": "https://servicewechat.com/wxad60dd8123a62329/322/page-frame.html"
    }

    try:
        # 发送POST请求
        see_match_response = requests.post(see_match_url, headers=see_match_headers, json=see_match_data)

        # 检查响应状态码
        if see_match_response.status_code == 200:
            # 解析JSON响应
            result = see_match_response.json()

            # 检查是否成功获取数据
            if result.get("opFlag") and result.get("code") == 200:
                see_match_data = result.get("see_match_data", {})
                show_farelevel_list = see_match_data.get("showFarelevelList", [])

                # 遍历票价级别列表
                for farelevel in show_farelevel_list:
                    salable_num = farelevel.get("salableNum", 0)
                    price = farelevel.get("price", 0)
                    verbose_name = farelevel.get("verboseName", "")

                    # 如果有票可售，打印信息
                    if salable_num > 0:
                        title = f"看个比赛！看个比赛！票价: {price}，区域: {verbose_name}，可售票数: {salable_num}"
                        print(title)
                        winsound.MessageBeep(winsound.MB_ICONASTERISK)  # 播放系统提示音
                        send_alert_email(title)
                        # 这里可以添加其他通知方式，比如发送邮件、短信等

                    # else:
                    #     print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} 没有可售票")
            else:
                print(f"获取数据失败，错误信息: {result.get('msg')}")
        else:
            print(f"请求失败，状态码: {see_match_response.status_code}")

        planet_response = requests.get(planet_url, headers=planet_headers)
        planet_response.raise_for_status()  # 检查请求是否成功
        data = planet_response.json()  # 解析JSON响应

        # 检查返回状态
        if data.get("statusCode") == 200 and data.get("data"):
            seat_plans = data["data"].get("seatPlans", [])
            for plan in seat_plans:
                seat_plan_name = plan.get("seatPlanName")
                can_buy_count = plan.get("canBuyCount", 0)
                original_price = plan.get("originalPrice")

                # 如果canBuyCount大于0，打印信息
                if can_buy_count > 0:
                    title = f"票星球！票星球！座位区域：{seat_plan_name}，价格：{original_price}元，可购票数：{can_buy_count}"
                    print(title)
                    winsound.MessageBeep(winsound.MB_ICONQUESTION)  # 播放系统提示音
                    send_alert_email(title)

        else:
            print(f"请求成功，但未获取到有效数据：{data.get('comments', '无返回信息')}")

    except requests.RequestException as e:
        print(f"请求失败：{e}")
    except json.JSONDecodeError as e:
        print(f"解析JSON失败：{e}")
    except Exception as e:
        print(f"发生错误: {e}")


def send_alert_email(title):
    """发送邮件提醒"""
    # 邮件配置（支持多个服务商）
    email_config = {
        "qq": {
            "smtp_server": "smtp.qq.com",
            "port": 465,
            "sender": os.getenv("QQ_EMAIL"),
            "password": os.getenv("QQ_PASSWORD")
        },
        "126": {
            "smtp_server": "smtp.126.com",
            "port": 465,
            "sender": os.getenv("126_EMAIL"),
            "password": os.getenv("126_PASSWORD")
        },
        "gmail": {
            "smtp_server": "smtp.gmail.com",
            "port": 587,
            "sender": os.getenv("GMAIL_EMAIL"),
            "password": os.getenv("GMAIL_PASSWORD")
        }
    }

    # 选择邮箱服务商（示例使用QQ邮箱）
    service = os.getenv("EMAIL_SERVIE_PROVIDER")
    config = email_config[service]

    # 创建邮件内容
    msg = MIMEMultipart()
    msg["From"] = config["sender"]

    # # 修改接收人配置
    # msg["To"] = "user1@example.com, user2@example.com"  # 直接多个地址
    # # 或者使用CC/BCC
    # msg["Cc"] = "copy@example.com"

    msg["To"] = "michael_scofied@126.com"  # 接收邮箱
    msg["Subject"] = title

    # 构建HTML内容
    html = f"""
    <html>
      <body>
        <h2 style="color:#2c3e50;">{title}</h2>
        <p style="color:#7f8c8d;">* 此邮件由自动监控系统生成，请勿直接回复</p>
      </body>
    </html>
    """

    # 添加HTML和纯文本双版本内容
    msg.attach(MIMEText(html, "html"))

    try:
        # 建立安全连接
        if service == "gmail":
            # Gmail需要TLS
            with smtplib.SMTP(config["smtp_server"], config["port"]) as server:
                server.starttls()
                server.login(config["sender"], config["password"])
                server.sendmail(config["sender"], msg["To"], msg.as_string())
        else:
            # QQ/126使用SSL
            with smtplib.SMTP_SSL(config["smtp_server"], config["port"]) as server:
                server.login(config["sender"], config["password"])
                server.sendmail(config["sender"], msg["To"], msg.as_string())

        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")


if __name__ == "__main__":
    winsound.MessageBeep(winsound.MB_ICONHAND)
    while True:
        monitor_tickets()
        # 每隔1秒执行一次
        time.sleep(0.5)
