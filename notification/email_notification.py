"""
邮件通知模块，用于发送邮件通知。
"""

# Import built-in modules
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
import logging
from typing import List, Optional, Dict, Union, Any

# Import third-party modules
import pandas as pd

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailNotifier:
    """邮件通知类，用于发送邮件通知。"""
    
    def __init__(
        self, 
        smtp_server: str = "smtp.qq.com",
        smtp_port: int = 465,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        use_ssl: bool = True
    ):
        """
        初始化邮件通知类。
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP服务器端口
            sender_email: 发件人邮箱，如果为None则从环境变量EMAIL_SENDER获取
            sender_password: 发件人邮箱密码或授权码，如果为None则从环境变量EMAIL_PASSWORD获取
            use_ssl: 是否使用SSL连接
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email or os.environ.get('EMAIL_SENDER')
        self.sender_password = sender_password or os.environ.get('EMAIL_PASSWORD')
        self.use_ssl = use_ssl
        
        if not self.sender_email or not self.sender_password:
            logger.warning(
                "邮件发送者信息未配置。请设置环境变量EMAIL_SENDER和EMAIL_PASSWORD，"
                "或在初始化时提供sender_email和sender_password参数。"
            )
    
    def send_email(
        self,
        to_emails: Union[str, List[str]],
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        html_content: Optional[str] = None
    ) -> bool:
        """
        发送邮件。
        
        Args:
            to_emails: 收件人邮箱，可以是单个邮箱地址或邮箱地址列表
            subject: 邮件主题
            body: 邮件正文（纯文本）
            attachments: 附件文件路径列表
            html_content: HTML格式的邮件内容，如果提供则优先使用
            
        Returns:
            bool: 发送是否成功
        """
        if not self.sender_email or not self.sender_password:
            logger.error("邮件发送者信息未配置，无法发送邮件")
            return False
            
        # 确保to_emails是列表
        if isinstance(to_emails, str):
            to_emails = [to_emails]
            
        # 创建邮件
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = ", ".join(to_emails)
        
        # 添加纯文本内容
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        # 如果提供了HTML内容，添加HTML部分
        if html_content:
            message.attach(MIMEText(html_content, "html", "utf-8"))
            
        # 添加附件
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as attachment:
                        part = MIMEApplication(attachment.read())
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename={os.path.basename(file_path)}",
                        )
                        message.attach(part)
                else:
                    logger.warning(f"附件文件不存在: {file_path}")
        
        try:
            # 连接到SMTP服务器
            context = ssl.create_default_context() if self.use_ssl else None
            
            logger.info(f"正在连接到SMTP服务器: {self.smtp_server}:{self.smtp_port}")
            
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls(context=context)
                
            # 登录
            logger.info(f"正在尝试登录邮箱: {self.sender_email}")
            server.login(self.sender_email, self.sender_password)
            
            # 发送邮件
            logger.info(f"正在发送邮件到: {', '.join(to_emails)}")
            server.sendmail(self.sender_email, to_emails, message.as_string())
            
            # 关闭连接
            server.quit()
            
            logger.info(f"邮件已成功发送给: {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件时出错: {str(e)}")
            if hasattr(e, 'smtp_error'):
                logger.error(f"SMTP错误详情: {e.smtp_error}")
            if hasattr(e, 'smtp_code'):
                logger.error(f"SMTP错误代码: {e.smtp_code}")
            logger.error(f"邮件服务器: {self.smtp_server}:{self.smtp_port}")
            logger.error(f"发件人: {self.sender_email}")
            return False
            
    def send_report_email(
        self,
        to_emails: Union[str, List[str]],
        subject: str,
        report_content: Dict[str, Any],
        report_files: Optional[List[str]] = None,
        include_summary: bool = True
    ) -> bool:
        """
        发送报告邮件，包含策略分析结果。
        
        Args:
            to_emails: 收件人邮箱，可以是单个邮箱地址或邮箱地址列表
            subject: 邮件主题
            report_content: 报告内容字典，包含要在邮件中显示的数据
            report_files: 报告文件路径列表，将作为附件发送
            include_summary: 是否在邮件正文中包含摘要信息
            
        Returns:
            bool: 发送是否成功
        """
        # 生成邮件正文
        body = f"交易策略分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if include_summary and report_content:
            body += "报告摘要:\n"
            for key, value in report_content.items():
                if isinstance(value, pd.DataFrame):
                    body += f"\n{key}:\n"
                    body += value.to_string(index=True) + "\n"
                else:
                    body += f"{key}: {value}\n"
        
        # 生成HTML内容
        html_content = None
        if include_summary and report_content:
            html_parts = [
                f"<h2>交易策略分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h2>",
                "<h3>报告摘要:</h3>"
            ]
            
            for key, value in report_content.items():
                if isinstance(value, pd.DataFrame):
                    html_parts.append(f"<h4>{key}:</h4>")
                    html_parts.append(value.to_html(index=True))
                else:
                    html_parts.append(f"<p><strong>{key}:</strong> {value}</p>")
                    
            html_parts.append("<p>详细报告请查看附件。</p>")
            html_content = "".join(html_parts)
        
        # 发送邮件
        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            body=body,
            attachments=report_files,
            html_content=html_content
        )


def send_email_notification(
    to_emails: Union[str, List[str]],
    subject: str,
    body: str,
    attachments: Optional[List[str]] = None,
    html_content: Optional[str] = None,
    smtp_server: str = "smtp.qq.com",
    smtp_port: int = 465,
    sender_email: Optional[str] = None,
    sender_password: Optional[str] = None,
    use_ssl: bool = True
) -> bool:
    """
    发送邮件通知的便捷函数。
    
    Args:
        to_emails: 收件人邮箱，可以是单个邮箱地址或邮箱地址列表
        subject: 邮件主题
        body: 邮件正文（纯文本）
        attachments: 附件文件路径列表
        html_content: HTML格式的邮件内容，如果提供则优先使用
        smtp_server: SMTP服务器地址
        smtp_port: SMTP服务器端口
        sender_email: 发件人邮箱，如果为None则从环境变量EMAIL_SENDER获取
        sender_password: 发件人邮箱密码或授权码，如果为None则从环境变量EMAIL_PASSWORD获取
        use_ssl: 是否使用SSL连接
        
    Returns:
        bool: 发送是否成功
    """
    notifier = EmailNotifier(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        sender_email=sender_email,
        sender_password=sender_password,
        use_ssl=use_ssl
    )
    
    return notifier.send_email(
        to_emails=to_emails,
        subject=subject,
        body=body,
        attachments=attachments,
        html_content=html_content
    )
