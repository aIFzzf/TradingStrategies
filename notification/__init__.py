"""
通知模块，用于发送各种通知，包括邮件通知等。
"""

from .email_notification import EmailNotifier, send_email_notification

__all__ = ['EmailNotifier', 'send_email_notification']
