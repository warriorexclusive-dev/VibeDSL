# -*- coding: utf-8 -*-
"""pack the plugin into a vsix, offline, and install it

Dropping a folder into the extensions directory is not enough: the list shows
it, with its version, and the window never activates it and says nothing. So
it is packed, and a vsix is a zip with a fixed layout. No network, no vsce.
"""
import json
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
VS = os.path.dirname(HERE)
ROOT = os.path.dirname(VS)
SRC = os.path.join(VS, "plugin")
OUT = os.path.join(VS, "plugin", "vibe-writer-2.0.0.vsix")
STAGE = os.path.join(VS, ".stage")


def find_code():
    """the code command, on any machine, in this order

    The path was written down as %LOCALAPPDATA%\\Programs\\Microsoft VS Code
    and that works on exactly one machine of one kind. It is looked for now in
    four places, cheapest first, and the result is a path or None. None is a
    real answer: building the vsix does not need VS Code, only installing it
    does, so the build is allowed to finish without it and the install says
    what to do instead of a KeyError.
    """
    env = os.environ.get("CODE_CMD")
    if env and os.path.isfile(env):
        return env
    from shutil import which
    for name in ("code", "code.cmd", "code-insiders"):
        p = which(name)
        if p:
            return p
    home = os.path.expanduser("~")
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", "")
        for c in (os.path.join(local, "Programs", "Microsoft VS Code", "bin", "code.cmd"),
                  os.path.join(home, "AppData", "Local", "Programs",
                               "Microsoft VS Code", "bin", "code.cmd"),
                  r"C:\Program Files\Microsoft VS Code\bin\code.cmd"):
            if c and os.path.isfile(c):
                return c
    else:
        for c in ("/usr/bin/code", "/usr/local/bin/code",
                  "/snap/bin/code", "/Applications/Visual Studio Code.app/"
                  "Contents/Resources/app/bin/code"):
            if os.path.isfile(c):
                return c
    return None


FILES = ["package.json", "extension.js", "language-configuration.json"]

CT = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="js" ContentType="application/javascript"/>
  <Default Extension="vibe" ContentType="text/plain"/>
  <Default Extension="vsixmanifest" ContentType="text/xml"/>
  <Default Extension="md" ContentType="text/markdown"/>
</Types>
"""


def manifest(pkg):
    return """<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Language="en-US" Id="{name}" Version="{version}" Publisher="{publisher}"/>
    <DisplayName>{disp}</DisplayName>
    <Description xml:space="preserve">{desc}</Description>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
  </Assets>
</PackageManifest>
""".format(name=pkg["name"], version=pkg["version"], publisher=pkg["publisher"],
           disp=pkg["displayName"], desc=pkg["description"])


def main():
    with open(os.path.join(SRC, "package.json"), encoding="utf-8") as fh:
        pkg = json.load(fh)
    print("")
    print("  СБОРКА VSIX, БЕЗ СЕТИ")
    for f in FILES:
        p = os.path.join(SRC, f)
        if not os.path.isfile(p):
            print("  ОТКАЗАНО, нет файла %s" % f)
            return 1
    print("    файлов     %d, все на месте" % len(FILES))

    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    ext = os.path.join(STAGE, "extension")
    os.makedirs(os.path.join(ext, "specs"))
    for f in FILES:
        shutil.copyfile(os.path.join(SRC, f), os.path.join(ext, f))
    shutil.copyfile(os.path.join(SRC, "specs", "writer.vibe"),
                    os.path.join(ext, "specs", "writer.vibe"))
    with open(os.path.join(STAGE, "[Content_Types].xml"), "w",
              encoding="utf-8") as fh:
        fh.write(CT)
    with open(os.path.join(STAGE, "extension.vsixmanifest"), "w",
              encoding="utf-8") as fh:
        fh.write(manifest(pkg))

    if os.path.isfile(OUT):
        os.remove(OUT)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _, names in os.walk(STAGE):
            for n in names:
                full = os.path.join(base, n)
                z.write(full, os.path.relpath(full, STAGE).replace("\\", "/"))
    print("    собрано    %s, %d Б" % (os.path.basename(OUT), os.path.getsize(OUT)))

    with zipfile.ZipFile(OUT) as z:
        bad = z.testzip()
        if bad:
            print("  ОТКАЗАНО, архив битый: %s" % bad)
            return 1
        print("    архив      цел, %d записей" % len(z.namelist()))

    shutil.rmtree(STAGE, ignore_errors=True)

    print("")
    print("  УСТАНОВКА В VS CODE")
    code = find_code()
    if not code:
        print("    код не найден, но vsix собран, и этого достаточно:")
        print("      VS Code -> Extensions -> ... -> Install from VSIX")
        print("      файл     %s" % OUT)
        print("    или укажи сам:  set CODE_CMD=путь  и запусти снова")
        print("  ГОТОВО, СБОРКА БЕЗ УСТАНОВКИ, код 0")
        return 0
    print("    команда   %s" % code)
    p = subprocess.run([code, "--install-extension", OUT, "--force"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300)
    for l in ((p.stdout or "") + (p.stderr or "")).strip().split("\n"):
        if l.strip():
            print("    %s" % l.strip())
    print("    код %d" % p.returncode)
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
