# 🏖️ 退休进度条

一个适用于Windows系统的系统托盘应用，帮助你追踪退休进度。

## 功能特点

- 🏖️ 显示在Windows右下角系统托盘
- 📊 自动计算距离退休还有多少天（x年x月x日）
- 📅 考虑闰年和每月天数不同的情况
- 🔔 每月1号通知更新当月预计储蓄金额
- 💰 支持复利计算

## 使用方法

1. 下载 `退休进度条.exe` 文件
2. 双击运行即可
3. 首次运行会弹出设置窗口，输入：
   - 目标退休金额
   - 当前已有储蓄金额
   - 本月预计储蓄金额
   - 预期年化收益率（可为0）

4. 鼠标悬停在托盘图标上可查看详细信息
5. 右键点击图标可打开菜单进行设置

## 计算逻辑

- 按月复利计算
- 自动处理闰年（2月29天）
- 自动处理每月不同天数
- 从当前日期逐月模拟计算，直到达到目标金额

## 开发

### 本地构建

```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --name "退休进度条" retirement_app.py
```

### GitHub Actions自动构建

每次推送到main分支时，GitHub Actions会自动构建Windows EXE文件，并发布到Release页面。

## 文件说明

- `retirement_app.py` - 主程序代码
- `requirements.txt` - Python依赖
- `.github/workflows/build.yml` - GitHub Actions构建配置
- `config.json` - 用户配置文件（运行时生成）
