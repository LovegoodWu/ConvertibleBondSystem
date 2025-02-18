import pandas as pd
import akshare as ak
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from IPython.display import display
from dotenv import load_dotenv
import os

# 配置参数
EXCEL_PATH = "strategy/20250216.xlsx"  # 替换为你的Excel路径
ALERT_FILE_PATH = "./alert"
ALERT_FILE_NAME = "买入提醒_{}.csv".format(datetime.today().strftime("%Y%m%d"))
NEED_SEND_MAIL = False  # 是否需要发送邮件提醒

load_dotenv()  # 加载.env文件


def load_strategy():
    """读取策略Excel文件"""
    df = pd.read_excel(
        EXCEL_PATH,
        usecols="B,AE,AF,AG",
        header=0,
        names=["代码", "建仓线", "加仓线", "重仓线"],
        skiprows=2,  # 跳过前两行
        skipfooter=14,  # 跳过最后两行
    )
    df["代码"] = df["代码"].astype(str).str[2:].str.zfill(6)  # 统一为6位代码

    # 将列转换为数值类型，并将无法转换的值替换为 NaN，然后用 0 填充
    df["建仓线"] = pd.to_numeric(df["建仓线"], errors='coerce').fillna(0).round(3)
    df["加仓线"] = pd.to_numeric(df["加仓线"], errors='coerce').fillna(0).round(3)
    df["重仓线"] = pd.to_numeric(df["重仓线"], errors='coerce').fillna(0).round(3)

    # 重命名列
    df = df.rename(columns={"代码": "债券代码"})
    validate_strategy(df)

    return df


def get_real_time_data():
    """获取可转债实时数据"""
    spot_df = ak.bond_zh_hs_cov_spot()

    spot_df = spot_df.rename(columns={"symbol": "债券代码"})
    spot_df = spot_df.rename(columns={"name": "债券名称"})
    spot_df = spot_df.rename(columns={"trade": "最新价"})

    spot_df["最新价"] = pd.to_numeric(spot_df["最新价"], errors='coerce').fillna(100000).round(3)
    spot_df["债券代码"] = spot_df["债券代码"].astype(str).str[2:].str.zfill(6)

    return spot_df[["债券代码", "债券名称", "最新价"]]


def generate_alert(strategy_df, price_df):
    """生成买入提醒"""
    merged_df = pd.merge(
        strategy_df,
        price_df,
        on="债券代码",
        how="left"
    )

    alert_conditions = []
    for _, row in merged_df.iterrows():
        current_price = row["最新价"]
        alerts = []

        if current_price <= row["重仓线"]:
            alerts.append(f"重仓触发（当前价{current_price} ≤ 重仓线{row['重仓线']}）")
        elif current_price <= row["加仓线"]:
            alerts.append(f"加仓触发（当前价{current_price} ≤ 加仓线{row['加仓线']}）")
        elif current_price <= row["建仓线"]:
            alerts.append(f"建仓触发（当前价{current_price} ≤ 建仓线{row['建仓线']}）")

        if alerts:
            alert_conditions.append({
                "债券代码": row["债券代码"],
                "债券名称": row["债券名称"],
                "当前价格": current_price,
                "提醒详情": "；".join(alerts),
                "建仓线": row["建仓线"],
                "加仓线": row["加仓线"],
                "重仓线": row["重仓线"]
            })

    return pd.DataFrame(alert_conditions)


def main():
    # 加载策略
    strategy_df = load_strategy()

    # 获取实时数据
    price_df = get_real_time_data()

    # 生成提醒
    alert_df = generate_alert(strategy_df, price_df)

    # 输出结果
    if not alert_df.empty:
        full_path = os.path.join(ALERT_FILE_PATH, ALERT_FILE_NAME)
        alert_df.to_csv(full_path, index=False, encoding="utf-8")
        print(f"生成提醒文件：{ALERT_FILE_NAME}")

        # 发送提醒邮件
        send_alert_email(alert_df, full_path)
    else:
        print("今日无符合条件的买入信号")


def validate_strategy(df):
    """验证策略合理性"""
    # 检查价格顺序：建仓价 > 加仓价 > 重仓价
    invalid_rows = df[(df["建仓线"] != 0) & ((df["建仓线"] <= df["加仓线"]) | (df["加仓线"] <= df["重仓线"]))]
    if not invalid_rows.empty:
        print("警告：以下代码价格设置不合理")
        print(invalid_rows)


def send_alert_email(alert_df, full_file_path):
    if not NEED_SEND_MAIL:
        return

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
    msg["Subject"] = f"可转债买入提醒 - {pd.Timestamp.now().strftime('%Y-%m-%d')}"

    # 构建HTML内容
    html = f"""
    <html>
      <body>
        <h2 style="color:#2c3e50;">今日可转债买入提醒（{len(alert_df)}条）</h2>
        {alert_df.to_html(index=False, border=1, classes="dataframe", justify="center")}
        <p style="color:#7f8c8d;">* 此邮件由自动监控系统生成，请勿直接回复</p>
      </body>
    </html>
    """

    # 添加HTML和纯文本双版本内容
    msg.attach(MIMEText(html, "html"))
    msg.attach(MIMEText(alert_df.to_string(index=False), "plain"))

    # 在send_alert_email函数中添加：
    with open(full_file_path, "rb") as f:
        file_data = f.read()
        attachment = MIMEApplication(file_data, Name="买入提醒.csv")
        attachment["Content-Disposition"] = 'attachment; filename="买入提醒.csv"'
        msg.attach(attachment)

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
    main()
