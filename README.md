# XFY Reframer

给动画描改手术流程准备的小工具：把视频拆成关键帧，改完图后再一键合成回视频。

## 软件截图

![XFY Reframer 运行界面](docs/screenshot-main.png)

## 创作目的

做动画描改时，最麻烦的是“拆帧-改图-对时间-合成”这套重复操作。  
这个软件就是把这套流程做成可视化按钮操作，少折腾、多出片。

## 获取方式

1. 直接在本仓库 `release/` 文件夹下载安装包：`XFY_Reframer_Setup_win64.exe`
2. 或使用网盘直链下载：  
   https://pan.baidu.com/s/1d1w0sTeoIWE-Lk5ZBscMXw?pwd=n31f

## 主要功能

- 导入视频后自动创建项目
- 一键拆分关键帧
- 支持把外部修改好的图片批量导回
- 选择时间信息文件并预览
- 一键合成输出视频
- 全程图形界面操作，不需要命令行

## 项目结构

```text
XFY_Reframer/
├─ extract/      # 拆帧
├─ combine/      # 合成
├─ core/         # 核心逻辑
├─ ui/           # 图形界面
├─ installer/    # 安装包脚本
├─ dist/         # 程序打包输出
├─ release/      # 安装包输出
└─ README.md
```

## 创作者信息

- B站账号：小肥霙
- 主页：https://space.bilibili.com/452714637?spm_id_from=333.788.0.0
- 希望大家用的开心！
