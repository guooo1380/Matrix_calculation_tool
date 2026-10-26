"""Phase 2 + 3: install SDK packages, then assemble and sign the APK by hand.

Manual pipeline (no Gradle): aapt2 compile/link -> javac -> d8 -> repack zip
-> zipalign -> apksigner. Everything is local and offline after the SDK exists.
"""
import os
import shutil
import subprocess
import sys
import zipfile

try:  # pythonw has no console; a cp936 stdout cannot print javac's output
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001 - older interpreters
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # android-build/
REPO = os.path.dirname(BASE)
SDK = os.path.join(BASE, "sdk")
JDK = os.path.join(BASE, "jdk")
BUILD = os.path.join(BASE, "build")
APP_SRC = os.path.join(BASE, "app-src")
WEBAPP = os.path.join(REPO, "webapp")
DIST = os.path.join(REPO, "dist")
LOG = os.path.join(BASE, "build.log")

REPO_BASE = "https://dl.google.com/android/repository/"
REPO_INDEX = REPO_BASE + "repository2-3.xml"
MIRROR_BASE = "https://mirrors.cloud.tencent.com/AndroidSDK/"

APP_ID = "com.mathtools.matrix"
VERSION_NAME = "1.0.0"
VERSION_CODE = "1"
APK_NAME = "mathtools-1.0.0.apk"


def log(*args):
    line = " ".join(str(a) for a in args)
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        # console codepage (cp936 here) cannot show everything javac emits
        print(line.encode("ascii", "replace").decode("ascii"), flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def tool(*parts):
    return os.path.join(*parts)


SDKMANAGER = tool(SDK, "cmdline-tools", "latest", "bin", "sdkmanager.bat")
BUILD_TOOLS = tool(SDK, "build-tools", "34.0.0")
ANDROID_JAR = tool(SDK, "platforms", "android-34", "android.jar")

ENV = os.environ.copy()
ENV["JAVA_HOME"] = JDK
ENV["PATH"] = tool(JDK, "bin") + os.pathsep + ENV.get("PATH", "")


def run(args, stdin_data=None, check=True, quiet=False):
    shown = " ".join('"%s"' % a if " " in a else a for a in args)
    if not quiet:
        log("$ " + shown)
    proc = subprocess.run(
        args, env=ENV, input=stdin_data,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    text = proc.stdout.decode("utf-8", "replace").strip()
    if text and not quiet:
        for line in text.splitlines():
            log("  " + line)
    if check and proc.returncode != 0:
        log("!! FAILED rc=%d" % proc.returncode)
        raise SystemExit(proc.returncode)
    return proc.returncode, text


def bat(path, *args, **kwargs):
    return run(["cmd", "/c", path] + list(args), **kwargs)


# ---------------------------------------------------------------- phase 2: SDK
def _download(name, dest, bases=None):
    """Fetch one archive, trying mirrors before the origin.

    dl.google.com reaches this machine through a local proxy at ~200 KB/s, so a
    mirror is tried first; `bases` pins the origin for the index itself.
    """
    curl = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                        "System32", "curl.exe")
    for base in (bases or (MIRROR_BASE, REPO_BASE)):
        url = base + name
        log("  fetching %s" % url)
        if os.path.exists(curl):
            rc = subprocess.run([curl, "-L", "--fail", "-s", "-o", dest,
                                 "--max-time", "3600", "--connect-timeout", "20",
                                 "--retry", "3", "--retry-delay", "3", url],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
        else:
            import urllib.request
            try:
                with urllib.request.urlopen(url, timeout=120) as response, \
                        open(dest, "wb") as fh:
                    shutil.copyfileobj(response, fh)
                rc = 0
            except Exception as exc:  # noqa: BLE001 - try the next mirror
                log("    failed: %s" % exc)
                rc = 1
        if rc == 0 and os.path.exists(dest) and os.path.getsize(dest) > 1024:
            log("  got %-46s %.1f MB" % (name, os.path.getsize(dest) / 1048576.0))
            return dest
        if os.path.exists(dest):
            os.remove(dest)
    raise SystemExit("download failed: " + name)


def _archive_url(index_xml, package_path, prefer="windows"):
    """Find the real zip name for a package in Google's repository index."""
    import re
    start = index_xml.find('path="%s"' % package_path)
    if start < 0:
        raise SystemExit("package absent from repository index: " + package_path)
    chunk = index_xml[start:index_xml.find("</remotePackage>", start)]
    urls = re.findall(r"<url>([^<]+)</url>", chunk)
    for url in urls:
        if prefer in url:
            return url
    if not urls:
        raise SystemExit("no archives listed for " + package_path)
    return urls[0]


def _unpack(zip_path, target, marker):
    """Unpack stripping the single top-level directory, verified by `marker`."""
    log("  unpacking %s (%s)" % (os.path.basename(zip_path), marker))
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        hits = [n for n in names if n.endswith("/" + marker)]
        if not hits:
            raise SystemExit("%s not found inside %s" % (marker, zip_path))
        root = hits[0][: -len("/" + marker)]
        if os.path.isdir(target):
            shutil.rmtree(target)
        os.makedirs(target)
        for name in names:
            if not name.startswith(root + "/") or name.endswith("/"):
                continue
            out = os.path.join(target, name[len(root) + 1:].replace("/", os.sep))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with archive.open(name) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst)
    if not os.path.exists(os.path.join(target, marker)):
        raise SystemExit("unpack produced no " + marker)


def install_sdk():
    log("=" * 70)
    log("Phase 2 - Android SDK packages")
    if os.path.exists(ANDROID_JAR) and os.path.exists(tool(BUILD_TOOLS, "aapt2.exe")):
        log("already installed")
        return

    if os.path.exists(SDKMANAGER):
        log("using sdkmanager")
        log("accepting licenses")
        bat(SDKMANAGER, "--sdk_root=" + SDK, "--licenses",
            stdin_data=b"y\n" * 400, check=False)
        log("installing platforms;android-34 + build-tools;34.0.0")
        bat(SDKMANAGER, "--sdk_root=" + SDK,
            "platforms;android-34", "build-tools;34.0.0",
            stdin_data=b"y\n" * 400)
    else:
        # No cmdline-tools: resolve the two archives from Google's index and
        # lay them out exactly where sdkmanager would have put them.
        log("sdkmanager absent - downloading archives directly")
        downloads = os.path.join(BASE, "downloads")
        os.makedirs(downloads, exist_ok=True)
        index_path = os.path.join(downloads, "repository2-3.xml")
        if not os.path.exists(index_path) or os.path.getsize(index_path) < 100000:
            _download("repository2-3.xml", index_path, bases=(REPO_BASE,))
        with open(index_path, encoding="utf-8", errors="replace") as fh:
            index_xml = fh.read()
        for package, target, marker in (
                ("platforms;android-34", tool(SDK, "platforms", "android-34"),
                 "android.jar"),
                ("build-tools;34.0.0", BUILD_TOOLS, "aapt2.exe")):
            if os.path.exists(os.path.join(target, marker)):
                continue
            name = _archive_url(index_xml, package)
            zip_path = os.path.join(downloads, os.path.basename(name))
            if not (os.path.exists(zip_path) and os.path.getsize(zip_path) > 5 << 20):
                _download(name, zip_path)
            _unpack(zip_path, target, marker)

    for path in (ANDROID_JAR, tool(BUILD_TOOLS, "aapt2.exe"),
                 tool(BUILD_TOOLS, "d8.bat"), tool(BUILD_TOOLS, "apksigner.bat"),
                 tool(BUILD_TOOLS, "zipalign.exe")):
        log("  %-70s %s" % (os.path.relpath(path, BASE), os.path.exists(path)))
        if not os.path.exists(path):
            raise SystemExit("missing SDK component: " + path)


# ------------------------------------------------------------- phase 3: build
def make_icons(res_dir):
    from PIL import Image

    src = os.path.join(WEBAPP, "icon-512.png")
    image = Image.open(src).convert("RGBA")
    if image.width != image.height:
        side = max(image.size)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
        image = canvas
    for density, size in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96),
                          ("xxhdpi", 144), ("xxxhdpi", 192)):
        out_dir = os.path.join(res_dir, "mipmap-" + density)
        os.makedirs(out_dir, exist_ok=True)
        image.resize((size, size), Image.LANCZOS).save(
            os.path.join(out_dir, "ic_launcher.png"), "PNG", optimize=True)
    log("icons   generated 5 densities from webapp/icon-512.png")


OFFLINE_SCRIPT = (
    "<script>"
    "if(location.protocol==='file:'){"
    "document.documentElement.className+=' native-shell';"
    "var f=document.getElementById('feedback-open');"
    "if(f){f.style.display='none';}"
    "}"
    "</script>"
)


def stage():
    log("=" * 70)
    log("Phase 3 - assemble APK")
    if os.path.isdir(BUILD):
        shutil.rmtree(BUILD)
    os.makedirs(BUILD)

    stage_dir = os.path.join(BUILD, "app")
    assets_www = os.path.join(stage_dir, "assets", "www")
    os.makedirs(assets_www)
    shutil.copy2(os.path.join(APP_SRC, "AndroidManifest.xml"),
                 os.path.join(stage_dir, "AndroidManifest.xml"))
    shutil.copytree(os.path.join(APP_SRC, "res"), os.path.join(stage_dir, "res"))
    shutil.copytree(os.path.join(APP_SRC, "java"), os.path.join(stage_dir, "java"))
    make_icons(os.path.join(stage_dir, "res"))

    for name in ("index.html", "app.js", "style.css", "icon-512.png"):
        shutil.copy2(os.path.join(WEBAPP, name), os.path.join(assets_www, name))

    index_path = os.path.join(assets_www, "index.html")
    with open(index_path, encoding="utf-8") as fh:
        html = fh.read()
    if "</body>" in html:
        html = html.replace("</body>", OFFLINE_SCRIPT + "\n</body>", 1)
    else:
        html += OFFLINE_SCRIPT
    with open(index_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    log("staged  %s" % os.path.relpath(stage_dir, BASE))
    return stage_dir


def aapt2(stage_dir):
    compiled = os.path.join(BUILD, "res.zip")
    run([tool(BUILD_TOOLS, "aapt2.exe"), "compile", "--dir",
         os.path.join(stage_dir, "res"), "-o", compiled])
    unsigned = os.path.join(BUILD, "resources.apk")
    run([tool(BUILD_TOOLS, "aapt2.exe"), "link",
         "-o", unsigned,
         "-I", ANDROID_JAR,
         "--manifest", os.path.join(stage_dir, "AndroidManifest.xml"),
         "-R", compiled,
         "--min-sdk-version", "21",
         "--target-sdk-version", "34",
         "--version-code", VERSION_CODE,
         "--version-name", VERSION_NAME,
         "--no-version-vectors",
         "--auto-add-overlay"])
    return unsigned


def compile_java(stage_dir):
    classes = os.path.join(BUILD, "classes")
    os.makedirs(classes)
    sources = []
    for root, _dirs, files in os.walk(os.path.join(stage_dir, "java")):
        sources += [os.path.join(root, f) for f in files if f.endswith(".java")]
    run([tool(JDK, "bin", "javac.exe"),
         "-encoding", "UTF-8", "-source", "8", "-target", "8",
         "-bootclasspath", ANDROID_JAR, "-classpath", ANDROID_JAR,
         "-d", classes] + sources)
    class_files = []
    for root, _dirs, files in os.walk(classes):
        class_files += [os.path.join(root, f) for f in files if f.endswith(".class")]
    dex_dir = os.path.join(BUILD, "dex")
    os.makedirs(dex_dir)
    bat(tool(BUILD_TOOLS, "d8.bat"), "--lib", ANDROID_JAR, "--min-api", "21",
        "--output", dex_dir, *class_files)
    dex = os.path.join(dex_dir, "classes.dex")
    if not os.path.exists(dex):
        raise SystemExit("d8 produced no classes.dex")
    log("dex     %.1f KB" % (os.path.getsize(dex) / 1024.0))
    return dex


def repack(unsigned, dex, stage_dir):
    """Put classes.dex + assets into the APK; keep resources.arsc STORED."""
    out = os.path.join(BUILD, "packed.apk")
    with zipfile.ZipFile(unsigned) as src, \
            zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "resources.arsc":
                info = zipfile.ZipInfo(item.filename, item.date_time)
                info.compress_type = zipfile.ZIP_STORED
                dst.writestr(info, data)
            else:
                dst.writestr(item, data)
        dst.writestr("classes.dex", open(dex, "rb").read())
        assets_root = os.path.join(stage_dir, "assets")
        for root, _dirs, files in os.walk(assets_root):
            for name in files:
                full = os.path.join(root, name)
                arc = os.path.join("assets",
                                   os.path.relpath(full, assets_root)).replace("\\", "/")
                dst.writestr(arc, open(full, "rb").read())
    log("packed  %d entries, %.1f KB" % (
        len(zipfile.ZipFile(out).namelist()), os.path.getsize(out) / 1024.0))
    return out


def sign(packed):
    os.makedirs(DIST, exist_ok=True)
    aligned = os.path.join(BUILD, "aligned.apk")
    run([tool(BUILD_TOOLS, "zipalign.exe"), "-f", "-p", "4", packed, aligned])

    keystore = os.path.join(BASE, "mathtools-release.jks")
    password = "mathtools2026"
    if not os.path.exists(keystore):
        run([tool(JDK, "bin", "keytool.exe"), "-genkeypair",
             "-keystore", keystore, "-storetype", "PKCS12",
             "-alias", "mathtools", "-keyalg", "RSA", "-keysize", "2048",
             "-validity", "10000",
             "-storepass", password, "-keypass", password,
             "-dname", "CN=MathTools, OU=MathTools, O=MathTools, L=Beijing, ST=Beijing, C=CN"])

    final = os.path.join(DIST, APK_NAME)
    bat(tool(BUILD_TOOLS, "apksigner.bat"), "sign",
        "--ks", keystore, "--ks-pass", "pass:" + password,
        "--key-pass", "pass:" + password,
        "--ks-key-alias", "mathtools",
        "--out", final, aligned)
    bat(tool(BUILD_TOOLS, "apksigner.bat"), "verify", "--print-certs", final)

    # Native build-tools only get ASCII paths; the user-facing copy is renamed in
    # Python so the delivered filename matches the Windows build (矩阵计算工具.exe).
    desktop_name = os.path.join(DIST, "矩阵计算工具.apk")
    shutil.copy2(final, desktop_name)
    os.remove(final)
    idsig = final + ".idsig"  # apksigner v4 sidecar; only needed for streaming install
    if os.path.exists(idsig):
        os.remove(idsig)
    log("APK     %s (%.2f MB)" % (desktop_name, os.path.getsize(desktop_name) / 1048576.0))
    return desktop_name


def main():
    open(LOG, "w", encoding="utf-8").close()
    log("build   repo=%s" % REPO)
    install_sdk()
    stage_dir = stage()
    unsigned = aapt2(stage_dir)
    dex = compile_java(stage_dir)
    packed = repack(unsigned, dex, stage_dir)
    final = sign(packed)
    log("PHASE3 OK " + final)


if __name__ == "__main__":
    main()
