#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
退休进度条 - 轻量版 (pystray + tkinter)
"""

import os
import sys
import json
import threading
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import customtkinter as ctk

# 尝试导入 pystray，如果失败给出提示
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    print("请先安装依赖: pip install pystray pillow python-dateutil")
    sys.exit(1)

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')


def create_icon():
    """创建沙滩伞图标"""
    # 64x64 的图标
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 伞顶 - 半圆形 (橙色)
    draw.pieslice([8, 8, 56, 48], 0, 180, fill=(255, 165, 0))

    # 伞条纹 (黄色)
    draw.pieslice([8, 8, 56, 48], 0, 60, fill=(255, 255, 0))
    draw.pieslice([8, 8, 56, 48], 120, 180, fill=(255, 255, 0))

    # 伞杆 (棕色)
    draw.rectangle([30, 28, 34, 56], fill=(139, 69, 19))

    return img


def load_config():
    """加载配置"""
    default = {
        'target_amount': 5000000,
        'current_amount': 100000,
        'monthly_saving': 5000,
        'annual_return': 3.0,
        'last_monthly_check': datetime.now().strftime('%Y-%m')
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                default.update(json.load(f))
        except:
            pass

    return default


def save_config(config):
    """保存配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'保存配置失败: {e}')


def calculate_retirement_date(config):
    """计算退休日期"""
    target = config.get('target_amount', 0)
    current = config.get('current_amount', 0)
    monthly = config.get('monthly_saving', 0)
    annual_rate = config.get('annual_return', 0) / 100

    if current >= target:
        return datetime.now(), 0

    if monthly <= 0 and annual_rate <= 0:
        return None, -1

    today = datetime.now()
    current_date = today
    accumulated = current
    months = 0
    max_months = 12 * 100
    monthly_rate = annual_rate / 12

    while accumulated < target and months < max_months:
        # 获取下个月的第一天
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1, day=1)

        accumulated += monthly
        accumulated *= (1 + monthly_rate)
        months += 1

    if accumulated >= target:
        return current_date, months

    return None, -1


def format_tooltip(config):
    """格式化托盘提示文本"""
    retirement_date, months = calculate_retirement_date(config)

    if retirement_date is None:
        return "🏖️ 退休进度条\n\n无法达到目标！\n请增加月储蓄金额或收益率"

    if months == 0:
        return "🏖️ 退休进度条\n\n🎉 恭喜！您已可以退休！"

    today = datetime.now()
    delta = relativedelta(retirement_date, today)
    days_total = (retirement_date - today).days

    progress = (config.get('current_amount', 0) / config.get('target_amount', 1)) * 100

    return (f"🏖️ 退休进度条\n"
            f"\n"
            f"目标: ¥{config.get('target_amount', 0):,.0f}\n"
            f"当前: ¥{config.get('current_amount', 0):,.0f}\n"
            f"进度: {progress:.1f}%\n"
            f"\n"
            f"预计退休: {retirement_date.strftime('%Y年%m月%d日')}\n"
            f"剩余: {delta.years}年{delta.months}月{delta.days}日 ({days_total}天)")


def show_settings(config, icon=None):
    """显示设置对话框 (CustomTkinter - Win11/macOS风格)"""
    # 设置外观
    ctk.set_appearance_mode('system')  # 跟随系统主题
    ctk.set_default_color_theme('blue')

    root = ctk.CTk()
    root.title('退休进度条 - 设置')
    root.geometry('420x480')
    root.resizable(False, False)

    # 居中窗口
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (420 // 2)
    y = (root.winfo_screenheight() // 2) - (480 // 2)
    root.geometry(f'+{x}+{y}')

    # 标题
    title_label = ctk.CTkLabel(
        root,
        text='退休进度条',
        font=('Microsoft YaHei', 22, 'bold')
    )
    title_label.pack(pady=(25, 8))

    # 副标题
    subtitle = ctk.CTkLabel(
        root,
        text='配置您的退休计划',
        font=('Microsoft YaHei', 12),
        text_color='gray'
    )
    subtitle.pack(pady=(0, 25))

    # 表单区域
    form_frame = ctk.CTkFrame(root, fg_color='transparent')
    form_frame.pack(fill='x', padx=35)

    # 目标金额
    ctk.CTkLabel(form_frame, text='目标退休金额', font=('Microsoft YaHei', 11)).pack(anchor='w', pady=(12, 5))
    target_entry = ctk.CTkEntry(form_frame, placeholder_text='例如：5000000', height=38, font=('Microsoft YaHei', 11))
    target_entry.pack(fill='x')
    target_entry.insert(0, str(config.get('target_amount', 5000000)))

    # 当前金额
    ctk.CTkLabel(form_frame, text='当前已有储蓄', font=('Microsoft YaHei', 11)).pack(anchor='w', pady=(18, 5))
    current_entry = ctk.CTkEntry(form_frame, placeholder_text='例如：100000', height=38, font=('Microsoft YaHei', 11))
    current_entry.pack(fill='x')
    current_entry.insert(0, str(config.get('current_amount', 100000)))

    # 月储蓄
    ctk.CTkLabel(form_frame, text='每月预计储蓄', font=('Microsoft YaHei', 11)).pack(anchor='w', pady=(18, 5))
    monthly_entry = ctk.CTkEntry(form_frame, placeholder_text='例如：5000', height=38, font=('Microsoft YaHei', 11))
    monthly_entry.pack(fill='x')
    monthly_entry.insert(0, str(config.get('monthly_saving', 5000)))

    # 收益率
    ctk.CTkLabel(form_frame, text='预期年化收益率 (%)', font=('Microsoft YaHei', 11)).pack(anchor='w', pady=(18, 5))
    return_entry = ctk.CTkEntry(form_frame, placeholder_text='例如：3.0', height=38, font=('Microsoft YaHei', 11))
    return_entry.pack(fill='x')
    return_entry.insert(0, str(config.get('annual_return', 3.0)))

    # 错误提示标签
    error_label = ctk.CTkLabel(root, text='', font=('Microsoft YaHei', 10), text_color='#FF6B6B')
    error_label.pack(pady=(15, 0))

    def on_save():
        try:
            config['target_amount'] = float(target_entry.get())
            config['current_amount'] = float(current_entry.get())
            config['monthly_saving'] = float(monthly_entry.get())
            config['annual_return'] = float(return_entry.get())
            save_config(config)
            if icon:
                icon.title = format_tooltip(config)
            root.destroy()
        except ValueError:
            error_label.configure(text='⚠️ 请输入有效的数字！')

    def on_cancel():
        root.destroy()

    # 按钮区域
    btn_frame = ctk.CTkFrame(root, fg_color='transparent')
    btn_frame.pack(pady=25)

    ctk.CTkButton(
        btn_frame,
        text='取消',
        command=on_cancel,
        width=110,
        height=38,
        fg_color='transparent',
        border_width=1,
        text_color=('gray10', 'gray90'),
        font=('Microsoft YaHei', 11)
    ).pack(side='left', padx=8)

    ctk.CTkButton(
        btn_frame,
        text='保存设置',
        command=on_save,
        width=110,
        height=38,
        font=('Microsoft YaHei', 11, 'bold')
    ).pack(side='left', padx=8)

    root.mainloop()


def show_monthly_dialog(config, icon):
    """显示月度更新对话框 (CustomTkinter)"""
    ctk.set_appearance_mode('system')
    ctk.set_default_color_theme('blue')

    root = ctk.CTk()
    root.title('更新月储蓄金额')
    root.geometry('350x220')
    root.resizable(False, False)

    # 居中窗口
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (350 // 2)
    y = (root.winfo_screenheight() // 2) - (220 // 2)
    root.geometry(f'+{x}+{y}')

    # 标题
    ctk.CTkLabel(
        root,
        text='📅 月度储蓄更新',
        font=ctk.CTkFont(size=16, weight='bold')
    ).pack(pady=(20, 10))

    # 日期显示
    today_str = datetime.now().strftime('%Y年%m月%d日')
    ctk.CTkLabel(
        root,
        text=f'今天是 {today_str}',
        font=ctk.CTkFont(size=12),
        text_color='gray'
    ).pack(pady=(0, 15))

    # 输入框
    ctk.CTkLabel(root, text='本月预计储蓄金额（元）', font=ctk.CTkFont(size=12)).pack(anchor='w', padx=30)
    entry = ctk.CTkEntry(root, placeholder_text='例如：5000', height=35)
    entry.pack(fill='x', padx=30, pady=(5, 15))
    entry.insert(0, str(config.get('monthly_saving', 5000)))

    def on_confirm():
        try:
            result = float(entry.get())
            if result < 0:
                return
            config['monthly_saving'] = result
            config['last_monthly_check'] = datetime.now().strftime('%Y-%m')
            save_config(config)
            icon.title = format_tooltip(config)
            root.destroy()
        except ValueError:
            pass

    def on_skip():
        root.destroy()

    # 按钮
    btn_frame = ctk.CTkFrame(root, fg_color='transparent')
    btn_frame.pack(pady=10)

    ctk.CTkButton(
        btn_frame,
        text='跳过',
        command=on_skip,
        width=80,
        height=32,
        fg_color='transparent',
        border_width=1,
        text_color=('gray10', 'gray90')
    ).pack(side='left', padx=5)

    ctk.CTkButton(
        btn_frame,
        text='确认',
        command=on_confirm,
        width=80,
        height=32,
        font=ctk.CTkFont(weight='bold')
    ).pack(side='left', padx=5)

    root.mainloop()


def check_monthly_reminder(config, icon):
    """检查月度提醒"""
    current_month = datetime.now().strftime('%Y-%m')
    last_check = config.get('last_monthly_check', '')

    if current_month != last_check and datetime.now().day == 1:
        # 延迟一下再显示，等托盘初始化完成
        threading.Timer(2, lambda: show_monthly_dialog(config, icon)).start()


def run_tray():
    """运行系统托盘"""
    config = load_config()

    # 创建图标
    icon_image = create_icon()

    # 创建菜单
    def on_settings(icon, item):
        show_settings(config, icon)

    def on_refresh(icon, item):
        icon.title = format_tooltip(config)

    def on_exit(icon, item):
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem('设置', on_settings),
        pystray.MenuItem('刷新', on_refresh),
        pystray.MenuItem('退出', on_exit)
    )

    # 创建托盘图标
    icon = pystray.Icon(
        'retirement',
        icon_image,
        format_tooltip(config),
        menu
    )

    # 检查月度提醒
    check_monthly_reminder(config, icon)

    # 首次运行显示设置
    if not os.path.exists(CONFIG_FILE):
        threading.Timer(1, lambda: show_settings(config, icon)).start()

    # 运行
    icon.run()


if __name__ == '__main__':
    run_tray()
