# XFY Reframer

给动画描改手书流程准备的小工具：把视频拆成关键帧，改完图后再一键合成回视频。

## 软件截图

### 拆帧界面

<img width="1421" height="929" alt="屏幕截图 2026-02-20 001313" src="https://github.com/user-attachments/assets/cdabbce5-5b29-435d-a88b-306f6eba1d6f" />


### 合成界面

<img width="1420" height="933" alt="屏幕截图 2026-02-20 001339" src="https://github.com/user-attachments/assets/8f730e8d-b8ff-47ae-b193-d57ebc6d2a5d" />


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
