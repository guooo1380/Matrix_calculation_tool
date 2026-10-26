# 打包安卓 APK（WebView 壳路线）

> 这条路线已经跑通并产出可安装的 APK。旧的 Kivy/Buildozer 路线见 [打包-Android.md](打包-Android.md)，它在本机没有成功过。

## 为什么换成这条路

程序本来就有两套界面可以搬到手机上：

| 路线 | 要编译什么 | 首次构建下载量 | 状态 |
|---|---|---|---|
| Kivy + Buildozer | CPython + Kivy + NDK 交叉编译 | 10–15 GB | 本机未成功（cython 钉版本、Gradle、NDK 链路脆弱） |
| **WebView 壳（本文）** | 一个 `MainActivity.java` + `webapp/` 静态资源 | 约 300 MB（JDK 179 + platform 60 + build-tools 56） | **已产出 APK** |

`webapp/` 本来就是为手机竖屏写的界面（`viewport`、`100dvh`、62px 输入格、五个运算都齐），WebView 只需原样加载它，计算全部在 JS 里完成，**不需要把 Python 搬上手机**。这样既不用 NDK，也不用 Gradle——手工调 `aapt2`/`javac`/`d8`/`zipalign`/`apksigner` 就能出包。

## 产物

| 项 | 值 |
|---|---|
| 文件 | `dist/矩阵计算工具.apk` |
| applicationId | `com.mathtools.matrix` |
| 应用名 | 矩阵计算工具 |
| versionName / versionCode | `1.0.0` / `1` |
| minSdk / targetSdk | 21（Android 5.0）/ 34（Android 14） |
| 架构 | 无原生库，全 ABI 通用 |
| 权限 | 不申请任何权限 |
| 图标 | 由 `webapp/icon-512.png` 生成的 5 档 mipmap |
| 联网 | 完全离线，只加载 `file:///android_asset/www/` |

## 源码位置

```
android-build/
├── app-src/                        # 壳工程（需要提交）
│   ├── AndroidManifest.xml
│   ├── res/values/strings.xml
│   └── java/com/mathtools/matrix/MainActivity.java
├── scripts/build_apk.py            # 一条命令跑完整个打包流程
├── downloads/  jdk/  sdk/  build/  # 工具链与中间产物（.gitignore 已排除）
└── mathtools-release.jks           # 签名用的 keystore（已排除，见下）
```

## 重新构建

```bash
python android-build/scripts/build_apk.py
```

脚本是幂等的：工具链、SDK 组件、keystore 已存在就跳过，只重做资源与代码部分。日志同时写到 `android-build/build.log`。

### 脚本做的事

1. **SDK 组件**：本机没有 `cmdline-tools`，所以脚本直接读 Google 的 [`repository2-3.xml`](https://dl.google.com/android/repository/repository2-3.xml) 索引，从里面解析出 `platforms;android-34` 与 `build-tools;34.0.0` 的真实归档名（**不能靠猜**：`platform-34_r03.zip` 之类的名字全是 404，实际叫 `platform-34-ext7_r03.zip`），下载后按 zip 内 `android.jar` / `aapt2.exe` 的位置剥掉顶层目录，落到 `android-build/sdk/` 下 `sdkmanager` 本该放的位置。有 `cmdline-tools` 时会走 `sdkmanager --sdk_root=...` 那条路。
   - 本机到 `dl.google.com` 只有约 200 KB/s（走本地代理 UniClash），两个包合计约 110 MB 要等十分钟；脚本会先试腾讯镜像 `mirrors.cloud.tencent.com/AndroidSDK/`，那里速度正常。
   - 下载的 zip 缓存在 `android-build/downloads/`，重跑不会重复下。
2. **资源**：`aapt2 compile --dir res -o res.zip` → `aapt2 link -I android.jar --manifest ... -R res.zip --min-sdk-version 21 --target-sdk-version 34`。
3. **图标**：Pillow 把 `webapp/icon-512.png` 缩成 mdpi 48 / hdpi 72 / xhdpi 96 / xxhdpi 144 / xxxhdpi 192 五档。
4. **静态资源**：`webapp/` 拷进 `assets/www/`，并在 `index.html` 的 `</body>` 前注入一段脚本——`file://` 打开时隐藏「建议」按钮（页面里的反馈表单是 Netlify 表单，离线壳里没有后端，`fetch('/')` 必然失败）。
5. **Java**：`javac -source 8 -target 8 -bootclasspath android.jar` 编译 `MainActivity.java`。
6. **dex**：`d8 --lib android.jar --min-api 21`。
7. **合包**：用 Python `zipfile` 把 `classes.dex` 和 `assets/` 塞进 aapt2 的产物；**`resources.arsc` 必须保持 STORED（不压缩）**，否则 Android 11+ 装不上。
8. **对齐**：`zipalign -f -p 4`。
9. **签名**：`apksigner sign`，然后 `apksigner verify --print-certs` 自检。

## 验证结果（2026-10-26 实际产物）

`aapt2 dump badging` / `apksigner verify` / `zipfile` 逐项查过：

| 检查项 | 结果 |
|---|---|
| 文件大小 | 447,538 B（0.43 MB） |
| SHA-256 | `30b7f1ddd237005831309415b81182b1ba7cde94716c5d53ff04e942def516a5` |
| 包名 / 版本 | `com.mathtools.matrix` / `1.0.0`(1) |
| minSdk / targetSdk | 21 / 34 |
| 应用名 | 矩阵计算工具（`application-label` 与 `launchable-activity` 都正确） |
| 图标 | 5 档密度齐全（160/240/320/480/640 dpi） |
| 权限 | 一条都没有（`aapt2 dump permissions` 只输出包名） |
| 屏幕 | 只声明竖屏，`small`–`xlarge` 全支持 |
| 签名 | v1(JAR) + v2 + v3 全部 `true`，证书 `CN=MathTools`，RSA 2048 |
| `resources.arsc` | STORED（未压缩），满足 Android 11+ 的安装要求 |
| `classes.dex` | 存在，3.3 KB（只有一个 Activity） |
| `assets/www/` | `app.js` / `style.css` / `icon-512.png` 与 `webapp/` **逐字节相同**；`index.html` 只多出注入的 180 B 脚本 |
| 注入脚本 | 命中：`location.protocol==='file:'` 时隐藏「建议」按钮 |
| JS 语法 | `node --check` 对打进包的 `app.js` 返回 0 |

**没做的验证**：本机没有安卓设备、也没有装模拟器（无 `adb`、无 `emulator`），所以**没有在真机/模拟器上跑过一次**。上面这些只能证明包结构、签名、资源都合法，不能证明运行期没有意外。第一次装到手机上时请留意这条。

## 关于签名

首次构建会生成 `android-build/mathtools-release.jks`（PKCS12，别名 `mathtools`，口令 `mathtools2026`，有效期 10000 天）。

**这是开发用的自签名证书**，能给真机安装、能侧载分发，但不适合上架应用商店。要发布时换成自己的 keystore，并把它和口令放到仓库之外；keystore 换了就必须换 `applicationId` 或卸载重装，否则手机会拒绝覆盖安装。

## 安装

```bash
# 手机开 USB 调试后
adb install -r dist/矩阵计算工具.apk
```

或者把 APK 传到手机，用文件管理器点开安装（需要在系统设置里允许「安装未知来源应用」）。

## 已知的壳层行为

- 竖屏锁定：`android:screenOrientation="portrait"`。
- 状态栏颜色 `#4338CA`，与页面主题色一致；导航栏白色。
- 返回键：网页不能后退时直接退出（单页应用，没有历史栈）。
- 外链一律拦下（`shouldOverrideUrlLoading` 只放行 `file://`），避免误跳浏览器。
- 没有 `INTERNET` 权限，所以任何联网请求都会失败——这是设计上的离线保证。
