import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

import requests

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """通知渠道基类"""

    @abstractmethod
    def send(self, alert: Dict[str, Any]) -> bool:
        pass


class EmailNotification(NotificationChannel):
    """邮件通知"""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str, use_tls: bool = True):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def send(self, alert: Dict[str, Any]) -> bool:
        try:
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["Subject"] = f"[WalletMonitor] {alert.get('risk_level', 'low').upper()} - {alert.get('alert_type', 'unknown')}"

            body = self._format_alert(alert)
            msg.attach(MIMEText(body, "html"))

            recipients = alert.get("recipients", [])
            if not recipients:
                logger.warning("没有配置邮件接收者")
                return False

            msg["To"] = ", ".join(recipients)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"邮件发送成功: {alert.get('message')}")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    def _format_alert(self, alert: Dict[str, Any]) -> str:
        risk_colors = {"high": "#f5222d", "medium": "#faad14", "low": "#52c41a"}
        risk_color = risk_colors.get(alert.get("risk_level", "low"), "#1890ff")

        return f"""
        <html>
        <body>
            <h2 style="color: {risk_color};">WalletMonitor Alert</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>钱包地址</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert.get('wallet_address', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>区块链</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert.get('chain', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>告警类型</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert.get('alert_type', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>风险等级</strong></td><td style="padding: 8px; border: 1px solid #ddd; color: {risk_color};">{alert.get('risk_level', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>消息</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert.get('message', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>交易哈希</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert.get('transaction_hash', 'N/A')}</td></tr>
            </table>
        </body>
        </html>
        """


class TelegramNotification(NotificationChannel):
    """Telegram通知"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, alert: Dict[str, Any]) -> bool:
        try:
            text = self._format_alert(alert)
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(f"Telegram通知发送成功: {alert.get('message')}")
            return True
        except Exception as e:
            logger.error(f"Telegram通知发送失败: {e}")
            return False

    def _format_alert(self, alert: Dict[str, Any]) -> str:
        risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        emoji = risk_emoji.get(alert.get("risk_level", "low"), "⚪")

        return f"""
{emoji} <b>WalletMonitor Alert</b>

💰 <b>钱包:</b> <code>{alert.get('wallet_address', 'N/A')}</code>
⛓️ <b>链:</b> {alert.get('chain', 'N/A').upper()}
📋 <b>类型:</b> {alert.get('alert_type', 'N/A')}
⚠️ <b>风险:</b> {alert.get('risk_level', 'N/A').upper()}
📝 <b>消息:</b> {alert.get('message', 'N/A')}
🔍 <b>交易:</b> <code>{alert.get('transaction_hash', 'N/A')}</code>
        """


class DiscordNotification(NotificationChannel):
    """Discord Webhook通知"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, alert: Dict[str, Any]) -> bool:
        try:
            embed = self._build_embed(alert)
            payload = {"embeds": [embed]}

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(f"Discord通知发送成功: {alert.get('message')}")
            return True
        except Exception as e:
            logger.error(f"Discord通知发送失败: {e}")
            return False

    def _build_embed(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        risk_colors = {"high": 0xf5222d, "medium": 0xfaad14, "low": 0x52c41a}
        color = risk_colors.get(alert.get("risk_level", "low"), 0x1890ff)

        return {
            "title": "WalletMonitor Alert",
            "color": color,
            "fields": [
                {"name": "钱包地址", "value": f"`{alert.get('wallet_address', 'N/A')}`", "inline": True},
                {"name": "区块链", "value": alert.get('chain', 'N/A').upper(), "inline": True},
                {"name": "告警类型", "value": alert.get('alert_type', 'N/A'), "inline": True},
                {"name": "风险等级", "value": alert.get('risk_level', 'N/A').upper(), "inline": True},
                {"name": "消息", "value": alert.get('message', 'N/A'), "inline": False},
                {"name": "交易哈希", "value": f"`{alert.get('transaction_hash', 'N/A')}`", "inline": False},
            ],
        }


class WebhookNotification(NotificationChannel):
    """通用Webhook通知"""

    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {"Content-Type": "application/json"}

    def send(self, alert: Dict[str, Any]) -> bool:
        try:
            response = requests.post(
                self.webhook_url,
                json=alert,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            logger.info(f"Webhook通知发送成功: {alert.get('message')}")
            return True
        except Exception as e:
            logger.error(f"Webhook通知发送失败: {e}")
            return False


class AlertNotifier:
    """
    告警通知器，管理多个通知渠道并发送告警
    """

    def __init__(self):
        self._channels: List[NotificationChannel] = []

    def add_channel(self, channel: NotificationChannel):
        """添加通知渠道"""
        self._channels.append(channel)

    def remove_channel(self, channel: NotificationChannel):
        """移除通知渠道"""
        self._channels.remove(channel)

    def notify(self, alert: Dict[str, Any]) -> Dict[str, bool]:
        """
        发送告警通知到所有渠道
        
        Args:
            alert: 告警数据
            
        Returns:
            各渠道发送结果
        """
        results = {}
        for i, channel in enumerate(self._channels):
            try:
                results[f"channel_{i}"] = channel.send(alert)
            except Exception as e:
                logger.error(f"通知渠道 {i} 发送失败: {e}")
                results[f"channel_{i}"] = False
        return results


_notifier_instance: Optional[AlertNotifier] = None


def get_notifier() -> AlertNotifier:
    """获取全局通知器单例"""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = AlertNotifier()
    return _notifier_instance
