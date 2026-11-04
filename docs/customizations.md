# 已验收的设备定制

本 fork 保存 ThinkSmart View CD-18781Y 的代码级定制，**不是新的可刷镜像**。
没有重新构建或发布镜像，不替换上游 Release；刷机、分区和备份规则仍按原教程。

## 本次纳入

- GTK 底栏：语音助手、哔哩哔哩、洛雪音乐、后退、刷新、Wi-Fi 设置；深蓝配色、图标和至少 58px 触摸高度。
- 返回小麦先直接加载本机主页，确认实际 UI 就绪后取消计时；4 秒未就绪才退出浏览器，由原会话循环重开，不重启语音后台。
- 已配网后仍能进入原来的扫描、选网、输入密码页面；配网页面保持打开，离开后清理状态；远程页面不获得本机控制权限。
- 本机应用按固定名单启动，共享非阻塞文件锁，避免重复实例或同时运行两个原生媒体客户端。
- 可选网关补丁：Edge TTS 连接超时/可选代理、Open-Meteo 天气、明确天气查询的工具路由。新闻使用原有插件，主要是启用配置，没有新的新闻实现。

不恢复已移除的爱奇艺、抖音入口，不纳入失败的触屏/播放实验。不改变 GPU、内核、唤醒词或麦克风硬件访问方式。

## 部署边界

这是供审查和手动部署的源码分支，不自动更新当前设备。升级前先备份并比较本机改动。
`image/device-setup.sh files` 已增加导航模块安装，但该命令还有上游设备配置动作，**不要只为更新浏览器而整段重跑**。

已运行本镜像的设备备份相应文件后，可以仅安装这两份文件：

```sh
sudo install -m 755 kiosk/thinksmart-kiosk.py /usr/local/bin/
sudo install -m 644 kiosk/thinksmart_browser_navigation.py /usr/local/bin/
```

先关闭媒体窗口，再仅重开浏览器，不重启 Weston、麦克风或小智网关。先核对唯一浏览器的完整命令行，不能宽泛 `pkill python`。
媒体按钮仅在对应应用和包装器已安装时显示，安装后重开浏览器生效；基础镜像不自带应用。配网继续使用本机既有 welcome.html，不替换保存的网络。这是迁入 fork 时新增的打包保护，单测覆盖；没有部署到当前设备，双应用已装的界面不变。

## 可选 ARM64 媒体应用

验证版本：[bilibili-linux](https://github.com/msojocs/bilibili-linux) `1.20.0-1 arm64`、[LX Music](https://github.com/lyswhut/lx-music-desktop/releases/tag/v2.12.6) `2.12.6 arm64`。两者都是 Electron 应用，不能据此宣称为本机实现了硬解或轻量原生 UI。

下载 Linux ARM64 正式包，核对 release 资产校验值和 `dpkg-deb -f ./package.deb Package Version Architecture`，先以 `apt-get -s install ./package.deb` 检查依赖，再由所有者决定安装。不使用 x86 模拟或未知一键安装器。

LX 2.12.6 ARM64 已验证包 SHA256：

```text
72e5a8defec9618dad8055f7a33e821bb9af81c887f65d52c1402bd347937256
```

安装应用后执行：

```sh
sudo sh media/install-launchers.sh
```

此脚本只安装包装器/desktop 入口并备份旧文件，不下载软件、重启服务或清除用户数据。使用镜像原本的 ubuntu/uid1000、Wayland `wayland-1` 和 Pulse。保守使用软件渲染，不额外添加 `--no-sandbox`；上游 renderer 的沙箱状态仍需独立评估。

首次正常打开并关闭洛雪后，以 ubuntu 用户运行：

```sh
python3 media/configure_lx.py
```

只启用上游支持的启动全屏，保留音源、协议确认、账号、音量和其它设置，生成 600 权限的私有配置备份；检测到洛雪仍运行时拒绝写入。协议/登录由用户决定。播放音质建议先选 128k。

洛雪在线播放需要另选音源。当前设备的 HelloWorld 社区音源已实际出声，用户反馈排行榜歌曲基本可播；**本仓库不收录音源 JS、共享鉴权参数或设备 user_api.json**。按[官方规范](https://lxmusic.toside.cn/desktop/custom-source)和内容授权使用，不保证全平台、全曲库、付费曲目或长期可用。

实物结果：洛雪显示/触控、酷我 128k 单曲及用户试用的排行榜通过；B站播放后的画面、声音、暂停与拖动通过，但冷启动/起播仍慢。没有全量或长时压力测试。

## 可选小智网关补丁

网关是独立仓库，修改本镜像仓库不会自动更新它。`extras/hub/voice-weather.patch` 对应 [xiaozhi-hub-server](https://github.com/justhalfbit/xiaozhi-hub-server) 提交 `a6e9a8300025b5a2efd75dd4d6a37f36c55dab79`，仅含三个源文件差异和一个新天气模块。

```sh
sh extras/hub/apply.sh /path/to/xiaozhi-hub-server
```

先在副本验证。脚本核对版本、目标未修改及补丁适用性，重复应用不改动；不替换私有配置、不自动重启服务。不强制套用其它版本。

`extras/hub/config.example.yaml` 仅是无凭据字段示例，不可直接覆盖完整配置。后台启用 function_call 和原有天气/新闻工具，在当前实际条目中合并默认北京、天气 provider、天气优先路由和晓晓参数。模型密钥只在本机后台设置。

晓晓是 Edge **在线**语音，不是本地离线合成；硅基流动模型与语音服务是两条独立连接。默认代理为空，不依赖固定家庭局域网地址；换网后的直连仍取决于新网络，不能承诺任何网络都可用。[Open-Meteo](https://open-meteo.com/en/docs) 免费接口范围/限制须遵守服务条款，商业用途另核授权。

天气模块限制连接/总等待、校验时间和温度完整性，失败返回暂不可用，不编造天气。weather_tool_first 只对明确中文天气查询强制 get_weather，不对取消、配置问题、新闻或工具结果递归强制调用。

网关更新可能阻止或覆盖本地差异，更新前保存补丁、核对新版本并测试；不用强制 reset。现有镜像构建要求网关工作树干净且提交在发布分支上，应用本补丁后**不能直接当成新的发布镜像**：须先在独立维护的网关仓库纳入改动，再完成构建检查。

## 验证和隐私

本地检查不调用真实模型或付费语音：

```sh
(cd kiosk && python3 -m unittest test_lx_entry.py test_wifi_entry.py test_fast_home.py test_packaging.py)
(cd media && python3 -m unittest test_configure_lx.py)
```

应用补丁、依赖齐全的网关测试副本，用网关原有 Python 环境执行：

```sh
THINKSMART_HUB_ROOT=/path/to/xiaozhi-hub-server/main/xiaozhi-server \
  /path/to/gateway/.venv/bin/python /path/to/this-fork/extras/hub/test_voice_tools.py
```

测试用 mock 替代模型、TTS、天气请求，不等于新网络实时接口验收。未重做刷机、镜像构建或整机重启测试。

不提交设备镜像/原厂备份、Wi-Fi 配置、SSH 密钥、模型/GitHub令牌、后台密码、聊天日志、cookie、音乐源脚本或用户数据库。`.gitignore` 只是辅助，提交前仍要审查新增内容。
