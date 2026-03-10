#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
退休进度条应用 - Windows系统托盘应用
"""

import sys
import json
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QDialog,
                             QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QDoubleSpinBox, QMessageBox, QInputDialog)
from PyQt6.QtCore import QTimer, Qt, QDate
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')


class ConfigDialog(QDialog):
    """配置对话框"""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or {}
        self.init_ui()
        self.load_config()

    def init_ui(self):
        self.setWindowTitle('退休进度条 - 设置')
        self.setFixedSize(400, 350)

        layout = QVBoxLayout()

        # 目标退休金额
        layout.addWidget(QLabel('目标退休金额（元）:'))
        self.target_amount = QDoubleSpinBox()
        self.target_amount.setRange(0, 9999999999)
        self.target_amount.setDecimals(2)
        self.target_amount.setMaximumWidth(300)
        layout.addWidget(self.target_amount)

        # 当前储蓄金额
        layout.addWidget(QLabel('当前已有储蓄金额（元）:'))
        self.current_amount = QDoubleSpinBox()
        self.current_amount.setRange(0, 9999999999)
        self.current_amount.setDecimals(2)
        self.current_amount.setMaximumWidth(300)
        layout.addWidget(self.current_amount)

        # 本月预计储蓄金额
        layout.addWidget(QLabel('本月预计储蓄金额（元）:'))
        self.monthly_saving = QDoubleSpinBox()
        self.monthly_saving.setRange(0, 999999999)
        self.monthly_saving.setDecimals(2)
        self.monthly_saving.setMaximumWidth(300)
        layout.addWidget(self.monthly_saving)

        # 预期年化收益率
        layout.addWidget(QLabel('预期年化收益率（%）:'))
        self.annual_return = QDoubleSpinBox()
        self.annual_return.setRange(0, 100)
        self.annual_return.setDecimals(2)
        self.annual_return.setValue(3.0)
        self.annual_return.setMaximumWidth(300)
        layout.addWidget(self.annual_return)

        # 按钮
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton('保存')
        self.save_btn.clicked.connect(self.save_config)
        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_config(self):
        if self.config:
            self.target_amount.setValue(self.config.get('target_amount', 5000000))
            self.current_amount.setValue(self.config.get('current_amount', 100000))
            self.monthly_saving.setValue(self.config.get('monthly_saving', 5000))
            self.annual_return.setValue(self.config.get('annual_return', 3.0))

    def save_config(self):
        self.config = {
            'target_amount': self.target_amount.value(),
            'current_amount': self.current_amount.value(),
            'monthly_saving': self.monthly_saving.value(),
            'annual_return': self.annual_return.value(),
            'last_monthly_check': datetime.now().strftime('%Y-%m')
        }
        self.accept()


class RetirementApp:
    """退休进度条主应用"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.config = self.load_config()

        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon()
        self.create_icon()
        self.tray_icon.setVisible(True)

        # 创建菜单
        self.create_menu()

        # 更新托盘提示
        self.update_tooltip()

        # 设置定时器 - 每分钟更新一次
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_tooltip)
        self.timer.start(60000)  # 每分钟更新

        # 检查是否需要提醒更新月储蓄金额
        self.check_monthly_reminder()

        # 设置每月1号提醒的定时器
        self.setup_monthly_timer()

    def create_icon(self):
        """创建沙滩伞图标"""
        # 创建一个简单的图标，使用沙滩伞emoji风格
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制沙滩伞（简化版）
        # 伞顶 - 半圆形
        painter.setBrush(QColor(255, 165, 0))  # 橙色
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPie(8, 8, 48, 40, 0, 180 * 16)

        # 伞条纹
        painter.setBrush(QColor(255, 255, 0))  # 黄色
        painter.drawPie(8, 8, 48, 40, 0, 60 * 16)
        painter.drawPie(8, 8, 48, 40, 120 * 16, 60 * 16)

        # 伞杆
        painter.setBrush(QColor(139, 69, 19))  # 棕色
        painter.drawRect(30, 28, 4, 28)

        painter.end()

        self.tray_icon.setIcon(QIcon(pixmap))

    def create_menu(self):
        """创建右键菜单"""
        menu = QMenu()

        # 显示退休倒计时
        self.status_action = menu.addAction('计算中...')
        self.status_action.setEnabled(False)
        menu.addSeparator()

        # 设置
        settings_action = menu.addAction('设置')
        settings_action.triggered.connect(self.show_settings)

        # 刷新
        refresh_action = menu.addAction('刷新')
        refresh_action.triggered.connect(self.update_tooltip)

        menu.addSeparator()

        # 退出
        quit_action = menu.addAction('退出')
        quit_action.triggered.connect(self.quit)

        self.tray_icon.setContextMenu(menu)

    def load_config(self):
        """加载配置"""
        default_config = {
            'target_amount': 5000000,
            'current_amount': 100000,
            'monthly_saving': 5000,
            'annual_return': 3.0,
            'last_monthly_check': datetime.now().strftime('%Y-%m')
        }

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                print(f'加载配置失败: {e}')

        return default_config

    def save_config(self):
        """保存配置"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'保存配置失败: {e}')

    def calculate_retirement_date(self):
        """
        计算退休日期
        考虑闰年、每月不同天数、复利计算
        """
        target = self.config.get('target_amount', 0)
        current = self.config.get('current_amount', 0)
        monthly = self.config.get('monthly_saving', 0)
        annual_rate = self.config.get('annual_return', 0) / 100

        if current >= target:
            return datetime.now(), 0

        if monthly <= 0 and annual_rate <= 0:
            return None, -1  # 无法达到目标

        # 逐月模拟计算
        today = datetime.now()
        current_date = today
        accumulated = current
        months = 0
        max_months = 12 * 100  # 最多计算100年

        monthly_rate = annual_rate / 12

        while accumulated < target and months < max_months:
            # 获取下一个月的天数
            if current_date.month == 12:
                next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                # 处理月末日期问题（如1月31日到2月）
                try:
                    next_month = current_date.replace(month=current_date.month + 1, day=1)
                except ValueError:
                    # 如果日期无效（如1月31日到2月），设为下月1日
                    if current_date.month == 12:
                        next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
                    else:
                        next_month = current_date.replace(month=current_date.month + 1, day=1)

            # 添加月储蓄
            accumulated += monthly

            # 添加当月利息（按月复利）
            accumulated *= (1 + monthly_rate)

            months += 1
            current_date = next_month

        if accumulated >= target:
            return current_date, months

        return None, -1

    def update_tooltip(self):
        """更新托盘图标提示"""
        retirement_date, months = self.calculate_retirement_date()

        if retirement_date is None:
            tooltip = "🏖️ 退休进度条\n\n无法达到目标！\n请增加月储蓄金额或收益率"
            self.status_action.setText('无法达到目标！请设置参数')
        elif months == 0:
            tooltip = "🏖️ 退休进度条\n\n恭喜！您已可以退休！"
            self.status_action.setText('恭喜！您已可以退休！')
        else:
            today = datetime.now()
            delta = relativedelta(retirement_date, today)

            years = delta.years
            months_remain = delta.months
            days = delta.days

            # 计算到目标日期的天数差（考虑闰年）
            days_total = (retirement_date - today).days

            progress = (self.config.get('current_amount', 0) / self.config.get('target_amount', 1)) * 100

            tooltip = (f"🏖️ 退休进度条\n"
                      f"\n"
                      f"目标: ¥{self.config.get('target_amount', 0):,.2f}\n"
                      f"当前: ¥{self.config.get('current_amount', 0):,.2f}\n"
                      f"进度: {progress:.2f}%\n"
                      f"\n"
                      f"预计退休日期:\n"
                      f"{retirement_date.strftime('%Y年%m月%d日')}\n"
                      f"\n"
                      f"剩余时间:\n"
                      f"{years}年{months_remain}月{days}日\n"
                      f"(共 {days_total} 天)")

            self.status_action.setText(
                f'剩余 {years}年{months_remain}月{days}日 ({days_total}天)'
            )

        self.tray_icon.setToolTip(tooltip)

    def check_monthly_reminder(self):
        """检查是否需要提醒更新月储蓄金额"""
        current_month = datetime.now().strftime('%Y-%m')
        last_check = self.config.get('last_monthly_check', '')

        if current_month != last_check and datetime.now().day == 1:
            # 每月1号提醒
            self.show_monthly_reminder()
            self.config['last_monthly_check'] = current_month
            self.save_config()

    def setup_monthly_timer(self):
        """设置每月提醒定时器"""
        # 计算到下个月1号的时间
        today = datetime.now()
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1, hour=9, minute=0, second=0)
        else:
            next_month = today.replace(month=today.month + 1, day=1, hour=9, minute=0, second=0)

        # 计算毫秒数差
        ms_until_next = int((next_month - today).total_seconds() * 1000)

        # 设置一次性定时器
        self.monthly_timer = QTimer()
        self.monthly_timer.setSingleShot(True)
        self.monthly_timer.timeout.connect(self.on_monthly_timer)
        self.monthly_timer.start(ms_until_next)

    def on_monthly_timer(self):
        """每月定时器触发"""
        self.show_monthly_reminder()
        self.config['last_monthly_check'] = datetime.now().strftime('%Y-%m')
        self.save_config()

        # 重新设置下个月的定时器
        self.setup_monthly_timer()

    def show_monthly_reminder(self):
        """显示每月提醒"""
        text, ok = QInputDialog.getDouble(
            None,
            '更新月储蓄金额',
            f'今天是 {datetime.now().strftime("%Y年%m月%d日")}\n'
            f'请输入本月预计储蓄金额（元）:',
            value=self.config.get('monthly_saving', 5000),
            min=0,
            max=999999999,
            decimals=2
        )

        if ok:
            self.config['monthly_saving'] = text
            self.save_config()
            self.update_tooltip()

    def show_settings(self):
        """显示设置对话框"""
        dialog = ConfigDialog(None, self.config)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.config = dialog.config
            self.save_config()
            self.update_tooltip()

    def quit(self):
        """退出应用"""
        self.app.quit()

    def run(self):
        """运行应用"""
        # 首次运行显示设置
        if not os.path.exists(CONFIG_FILE):
            self.show_settings()

        sys.exit(self.app.exec())


if __name__ == '__main__':
    app = RetirementApp()
    app.run()
