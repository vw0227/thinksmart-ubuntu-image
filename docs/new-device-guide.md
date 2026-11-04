# 在另一台 ThinkSmart View 上部署本分支

文档核对日期：2026-11-04。先读本文，再按链接执行刷机原步骤，不要整篇一次粘贴运行。

## 1. 先确定适用范围

仅适用于 **Lenovo ThinkSmart View CD-18781Y，APQ8053/MSM8953、2GB 内存、8GB eMMC** 的另一台同型号设备，不适用于 ThinkSmart View Plus 或其它 ARM 机器。外壳相似、CPU 同系列不代表可刷。

本分支 `device-customizations-20261104` 是定制源码，不是刷机包。核对当日，本 fork 没有镜像 Release。**下载 GitHub 的 Source code ZIP 不能刷机。** 推荐路线：

```text
核对新设备 → 该设备独立整盘备份 → 按现有分区选 A/B 路线
→ 刷经过校验的上游基础镜像 → 新设备配网和安全设置
→ 安装本分支导航/可选媒体/网关补丁 → 逐项实物验收
```

想做“刷一次就带齐定制”的自有镜像，另见[镜像构建与发布前置条件](image-release-readiness.md)；当前没有交付或验证这种整合镜像。

## 2. 准备电脑、资料和每台机器的备份

- 原电源、可靠数据线、电脑本体 USB 接口、可用 Wi-Fi；电脑至少按[原教程准备](../README.md#0-准备)预留 20GB，做双份备份建议留更多。
- 按电脑系统安装 edl、libusb/USB 驱动、SSH、解压工具；不要把完整 Linux 命令直接粘到 PowerShell。原教程有 Windows 对照。
- Windows 10 上 EDL 和 bootstrap 的 USB NCM 网络是两回事。先准备好 Linux 环境或经确认的私有 bootstrap 配网方案，**在确认可进入 bootstrap 管理前，不执行改 GPT**。USB 直通也必须在所用虚拟机实际验证；不能假设远端 PVE 自动拥有本机 USB。
- [上游 FLASHING.md](https://github.com/rickx/ubuntu-thinksmart/blob/main/FLASHING.md)提供 bootstrap 准备脚本线索。若要注入 Wi-Fi，仅在获得所有者许可后制作私有副本，原文件不改，副本留本机不上传；这不代表本 fork 已提供 Windows 一键兼容方案。
- 公开源码可放 Git 工作目录；每台设备的镜像、凭据和日志放**仓库外的私有目录**。不要把新机器叫作旧机器的 IP；IP 是当前网络分配的地址。

每台机器单独建立目录，例如在仓库外使用 `device-001/`。保留型号、原始/改后 GPT、备份大小与校验、刷写日志和本次使用版本；用[验收表模板](device-checklist.md)，不填写密码或密钥。

**跨机器禁止事项：**

- 不向 B 机器刷 A 机器的 `stock-full-emmc.bin`，不迁移 `persist`、固件校准数据或序列号。
- 不把旧机器的整盘/私人系统镜像当成通用发行镜像。
- 不跨机器还原整包 userdata、SSH 主机私钥、machine-id、客户端设备 ID、浏览器 cookie 或聊天数据库；新机器独立生成身份。
- 管理员 SSH 公钥可由所有者选择授权给多台机器，但管理员私钥不复制进设备或仓库。

## 3. 选择并校验基础镜像

本次文档核对使用[上游 20261101 Release](https://github.com/justhalfbit/thinksmart-ubuntu-image/releases/tag/20261101)，不是“本 fork 已发布的定制镜像”。下载：

- [thinksmart-ubuntu-20261101.img.xz](https://github.com/justhalfbit/thinksmart-ubuntu-image/releases/download/20261101/thinksmart-ubuntu-20261101.img.xz)
- [SHA256SUMS](https://github.com/justhalfbit/thinksmart-ubuntu-image/releases/download/20261101/SHA256SUMS)
- 走原厂路线 A 还要按[原教程 0.3](../README.md#03-下载文件)下载 lk2nd、bootstrap 及其校验文件。

公开原始文件核对值如下，只适用于这个版本，不适用于加入 Wi-Fi 的私人副本：

| 文件 | 字节数 | SHA256 |
| --- | ---: | --- |
| `thinksmart-ubuntu-20261101.img.xz` | 711307968 | `3b3045c5ddc753dc61eb9815edc29a565485ba908c47524884f5fde119f9d942` |
| `thinksmart-ubuntu-20261101.img` | 3466592256 | `b412b4d417435810c683a501e0d0023ec189ca0097a050067fc997a2bfc9e7c2` |

Linux/macOS 按原教程校验下载和解压后的两个文件；Windows 用 `Get-FileHash`，7-Zip 解压。不匹配就停止，不能靠改校验文件让它“通过”。换基础镜像版本时重新核对整个兼容性，尤其网关补丁的基准提交。

## 4. EDL、备份和刷写

逐步使用[原刷机教程](../README.md)，其破坏性操作确认规则仍有效。这里列检查点，不把写盘步骤合并成一键脚本。

1. 按原教程 1.1 进入 EDL；黑屏本身不是成功证据，电脑还应枚举 Qualcomm 9008。
2. 只读 `edl printgpt`。必须确认 CPU `APQ8053`、`total_blocks:15269888`，型号标签也吻合。
3. `system` 为 1.5GB、仍有 userdata：走[路线 A](../README.md#路线-a第一次刷设备还是原厂系统)。先读全盘并验证，再刷 lk2nd/bootstrap，确认 bootstrap SSH 正常后才改 GPT。
4. `system` Length 为 `0x00000001b3cfbe00` 且无 userdata：走[路线 B](../README.md#路线-b已经刷过本镜像或上游-ubuntu-镜像)。先保留这台设备自己的现有数据备份；**不再运行 GPT helper**。
5. 其它布局、型号/容量不符、无法解释的输出：停止，不能猜偏移或照抄旧机器记录。

路线 A 的原厂全盘备份至少满足：大小 **7818182656 字节**、偏移 512 处为 `EFI PART`、保存 SHA256，并跨盘保留第二份。大小/GPT 签名和自校验不能证明每一个扇区都正确；条件允许再独立读回比较。备份失败不进入任何写盘步骤；不覆盖已有备份。

每次写入 boot/system、改 GPT、重刷前重新确认**目标设备、文件、校验、分区和数据损失**，由所有者同意后执行。不要从“写好说明”推定已经同意操作某一台新机器。不尝试 fastboot flash/erase/unlock，不写 modem/dsp/persist，不整盘克隆其它设备。

## 5. 新设备首次启动和基础验收

1. 等首次启动完成，在欢迎页扫描 Wi-Fi、选网络并输入新设备要使用的密码；保留物理麦克风隐私开关的控制权。
2. 电脑与设备同网，从屏幕或路由器 DHCP 表确认新 IP，再打开 `http://<新设备IP>:16688/admin`。网关加载模型可能比界面慢，未就绪不直接反复断电。
3. 新后台设置独立强密码。Ubuntu/root 的公开默认密码按[原教程 2.5](../README.md#25-改默认密码为了安全刷完马上改)立即更换；不要用示例数字或从聊天记录抄密码。
4. 若改为 SSH 公钥管理，先在第二个终端验证新设备公钥登录和 sudo，再关闭密码/root 远程登录。不要先锁住唯一可用入口；不复制旧设备 SSH 主机密钥，不跳过指纹核验。
5. 在设备 SSH 会话中检查：

   ```sh
   uname -m
   df -h /
   systemctl is-active thinksmart-kiosk thinksmart-client
   systemctl --user is-active pipewire wireplumber thinksmart-mic xiaozhi-hub
   curl --max-time 5 -fsS http://127.0.0.1:8090/api/health
   ```

   应是 aarch64、服务 active、health 的 audio/hub 为 true。但 health 不证明实际采集或播放，仍要实物测试。基础镜像预期有约 6GB 级根分区；如果仅约 3GB，先只读核对实际块设备和 ext4 状态。不要直接复制本机曾用的 loop 设备名运行 resize2fs，更不要为扩文件系统重改 GPT。

基础语音客户端是 0.1.0，后续更新可能不同。升级前记录版本，升级后再验收；不能把当前设备曾成功更新理解为任意未来版本均兼容。本机服务地址仍用 `127.0.0.1`，不要把网关改成旧机器或某台家庭虚拟机的 IP。后台只供可信局域网使用，不做公网端口转发。

## 6. 在新设备取得正确分支并安装导航

下面命令在**新设备的 ubuntu SSH 会话**执行；不在 Windows PowerShell 里直接执行，也不在当前旧设备上误跑。若已有同名目录，先查看内容，不覆盖。

```sh
git clone --single-branch --branch device-customizations-20261104 \
  https://github.com/vw0227/thinksmart-ubuntu-image.git ~/thinksmart-fork
cd ~/thinksmart-fork
git branch --show-current
git rev-parse HEAD
```

分支名应为 `device-customizations-20261104`。记录提交号；只下载默认 main 会漏掉这些定制。公开克隆不需要 GitHub 令牌，更不应把维护者令牌放到设备。

先通过离线检查，再备份当前浏览器：

```sh
(cd kiosk && python3 -m unittest test_lx_entry.py test_wifi_entry.py test_fast_home.py test_packaging.py)
(cd media && python3 -m unittest test_configure_lx.py)
umask 077
KIOSK_BACKUP=$(mktemp -d "$HOME/thinksmart-kiosk-backup.XXXXXX")
sudo cp -p /usr/local/bin/thinksmart-kiosk.py "$KIOSK_BACKUP/"
if [ -e /usr/local/bin/thinksmart_browser_navigation.py ]; then
    sudo cp -p /usr/local/bin/thinksmart_browser_navigation.py "$KIOSK_BACKUP/"
fi
printf 'Backup directory: %s\n' "$KIOSK_BACKUP"
```

记下模块原本是否存在和备份目录。然后仅安装两个浏览器文件（先模块后主程序）：

```sh
sudo install -m 644 kiosk/thinksmart_browser_navigation.py /usr/local/bin/
sudo install -m 755 kiosk/thinksmart-kiosk.py /usr/local/bin/
```

**不为这一步重跑 `device-setup.sh files/purge/tidy/codec`。** 关闭媒体窗口后，只对核对过完整命令行的唯一浏览器主进程发送 TERM：

```sh
ps -eo pid,args | grep '[p]ython3 /usr/local/bin/thinksmart-kiosk.py'
# 核对只有目标浏览器主进程，再将占位符换为刚查到的 PID：
kill -TERM <已核对的浏览器PID>
```

原会话会重开浏览器。不要 `pkill python`。`sudo kiosk-mode restart` 实际会重启整个 kiosk/Weston 服务，不等于只刷新页面，不作为首选。重开后应看到语音助手、后退、刷新和 Wi-Fi 设置；媒体按钮只在对应应用及包装器已安装后显示。

## 7. 配置模型、晓晓、天气和新闻

先让基础模型对“你好”正常回答，再逐项添加工具；不要同时更新所有组件。按[定制说明](customizations.md)配置，下面是关键顺序：

1. 后台选自定义 OpenAI 兼容模型，base URL 为 `https://api.siliconflow.cn/v1`。已验证模型 ID 是 `deepseek-ai/DeepSeek-V4.1-Flash`；在自己的账号核对是否仍可用、支持工具和余额/计费，再填自己的密钥。这里不提供共享密钥，不承诺模型长期供应或免费。
2. 可用时关闭深度思考以降低语音首字延迟；示例字段在 `extras/hub/config.example.yaml`。先问“你好”，分别观察识别文字、回答文字和声音。
3. 语音选 Edge 的 `zh-CN-XiaoxiaoNeural`（晓晓）。它仍需联网，不是硅基流动提供的音色，也不是离线合成；TTS 代理默认留空，不能依赖旧家庭地址。
4. 在设备上先读取 `git -C ~/xiaozhi-hub-server rev-parse HEAD` 和工作树状态。20261101 基础镜像网关基准为 `a6e9a8300025b5a2efd75dd4d6a37f36c55dab79`。不同版本或已有修改时停止迁入补丁，不强制 checkout/reset，不覆盖用户源文件。
5. 备份这台设备的网关私有 `data/` 和目标源码到仓库外的 700 目录，配置副本限制为 600。该目录含密码/模型密钥，禁止打印或上传；不要 `cat data/.config.yaml` 贴到聊天。
6. 回到 `~/thinksmart-fork`，应用守卫补丁：

   ```sh
   sh extras/hub/apply.sh /home/ubuntu/xiaozhi-hub-server
   THINKSMART_HUB_ROOT=/home/ubuntu/xiaozhi-hub-server/main/xiaozhi-server \
     /home/ubuntu/xiaozhi-hub-server/main/xiaozhi-server/.venv/bin/python \
     "$PWD/extras/hub/test_voice_tools.py"
   ```

   成功应通过 9 项 mock 测试。脚本不替你写私有配置，也不重启网关；缺依赖/版本不符不能记成通过。
7. 在后台或经审查的私有配置中合并示例字段：天气 provider=`open_meteo`、默认城市北京、所选自定义模型 `weather_tool_first=true`；启用 function_call 和原有 `get_weather`、`get_news_from_newsnow`、`get_news_from_chinanews`，保留其他工具。条目名以实际选中的配置为准；示例文件不能整份覆盖。
8. 保存、测试通过后，才执行一次 `systemctl --user restart xiaozhi-hub` 载入源代码改动。若后台热更新过配置，仍不代表旧 Python 进程已载入新源码。等健康恢复，再做实物问答。

Open-Meteo 不需要原和风天气密钥，但免费服务/商业授权和网络可达性要另行核对。新闻源也可能调整或不可达。“模型说没联网”不等于设备没 Wi-Fi，先看是否实际调用工具。插件启用不自动给模型新增通用网页浏览器。

## 8. 可选安装 B站和洛雪

先确认磁盘有余量，媒体不是语音正常运行的必需组件。2GB 内存不宜同时运行两个媒体客户端。下列是已验证版本，不自动追最新版：

| 应用 | 下载 | 包名/架构 | SHA256 |
| --- | --- | --- | --- |
| B站 `1.20.0-1` | [ARM64 deb](https://github.com/msojocs/bilibili-linux/releases/download/v1.20.0-1/io.github.msojocs.bilibili_1.20.0-1_arm64.deb) | `io.github.msojocs.bilibili` / arm64 | `1435290a75e8564a35654ad51784726fabec6e9e8623ef5e4936d39560b5759f` |
| 洛雪 `2.12.6` | [ARM64 deb](https://github.com/lyswhut/lx-music-desktop/releases/download/v2.12.6/lx-music-desktop_2.12.6_arm64.deb) | `lx-music-desktop` / arm64 | `72e5a8defec9618dad8055f7a33e821bb9af81c887f65d52c1402bd347937256` |

在设备或电脑下载，校验后传到新设备私有下载目录。对**每一个实际文件**先检查，不把占位符直接粘贴执行：

```sh
sha256sum ./<实际包名>.deb
dpkg-deb -f ./<实际包名>.deb Package Version Architecture
sudo apt-get -s install ./<实际包名>.deb
# 确认架构、空间、依赖及不会移除关键包后，用户同意再安装：
sudo apt-get install ./<实际包名>.deb
```

不解除关键包 hold，不运行整机升级来“凑依赖”。安装完成后回 `~/thinksmart-fork`：

```sh
sudo sh media/install-launchers.sh
```

此脚本只安装启动器/desktop 文件，旧文件备份在输出的 `/var/backups/thinksmart-media.*`，不安装包或重启服务。按第 6 节只重开浏览器后才出现媒体按钮。

洛雪第一次启动会生成配置；正常关闭后运行 `python3 media/configure_lx.py`，再开即可启用全屏。若第一次黑屏，先 SSH 核对唯一 LX 主进程再正常 TERM 退出，确认应用进程都已退出后再运行该配置工具；不盲目清空配置、不补丁 app.asar。

洛雪“有排行榜”不等于可播放。按[官方自定义源规范](https://lxmusic.toside.cn/desktop/custom-source)独立选择合法来源，经审查后在新设备导入并选中；不能从旧设备直接拷贝整个配置/数据库。本仓库不附音乐源 JS 或共享鉴权。先试 128k 单曲，再试切歌、暂停和恢复，不承诺全曲库或付费内容。

不安装爱奇艺和抖音，不恢复已放弃的播放/手势补丁；B站起播仍可能较慢。

## 9. 交付、换网和关机

逐项完成[新设备验收表](device-checklist.md)。至少包括：真实唤醒和问答、晓晓出声、北京明天天气的具体数据、一条新闻、Wi-Fi 换网后再次语音、导航回主页，以及选装应用的实际播放。只看进程、health、排行榜或返回 URL，不能算全部通过。

换网通过底栏 Wi-Fi 设置扫描、选网、输入密码；电脑也连同网再找新 IP。不要预设旧 IP 继续有效，也不要把旧代理写成必需。未做过的陌生网络单独标为未验证。

Ubuntu 正常关机用屏幕支持的关机入口或 `sudo systemctl halt`；黑屏后至少等 10 秒再拔电，断电约 30 秒再接回。设备插电自启，不用 `poweroff` 当常规关机。异常处理、备份恢复、更新边界见[维护与回退](maintenance-and-recovery.md)。
