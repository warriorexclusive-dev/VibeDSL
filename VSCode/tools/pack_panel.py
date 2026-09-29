# -*- coding: utf-8 -*-
"""pack the panel into a vsix, offline, and install it

The same shape as the writer's build and for the same reason: a folder dropped
into the extensions directory is listed and never activated. A vsix is a zip
with a fixed layout, and there is no network in this step.

    py -3 tools/pack_panel.py
"""
import json
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
VS = os.path.dirname(HERE)
REPO = os.path.dirname(VS)
SRC = os.path.join(VS, "panel")
OUT = os.path.join(SRC, "vibe-panel-2.0.0.vsix")
STAGE = os.path.join(VS, ".stage-panel")

CODE = os.environ.get("CODE_CMD")
if not CODE:
    from shutil import which
    CODE = None
    for n in ("code", "code.cmd", "code-insiders"):
        if which(n):
            CODE = which(n)
            break
if not CODE and os.name == "nt":
    local = os.environ.get("LOCALAPPDATA", "")
    for c in (os.path.join(local, "Programs", "Microsoft VS Code", "bin", "code.cmd"),
              os.path.join(REPO, r"AppData\Local\Programs\Microsoft VS Code\bin\code.cmd")):
        if os.path.isfile(c):
            CODE = c
            break

FILES = ["package.json", "extension.js", "icon.svg"]

CT = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="js" ContentType="application/javascript"/>
  <Default Extension="svg" ContentType="image/svg+xml"/>
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
    print("  СБОРКА VSIX ПАНЕЛИ, БЕЗ СЕТИ")
    for f in FILES:
        if not os.path.isfile(os.path.join(SRC, f)):
            print("  ОТКАЗАНО, нет файла %s" % f)
            return 1
    print("    файлов     %d, все на месте" % len(FILES))

    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    ext = os.path.join(STAGE, "extension")
    os.makedirs(ext)
    for f in FILES:
        shutil.copyfile(os.path.join(SRC, f), os.path.join(ext, f))
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
    print("  УСТАНОВКА")
    if not CODE:
        print("    code не найден, vsix собран:")
        print("      Extensions -> ... -> Install from VSIX")
        print("      %s" % OUT)
        return 0
    p = subprocess.run([CODE, "--install-extension", OUT, "--force"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300)
    for l in ((p.stdout or "") + (p.stderr or "")).strip().split("\n"):
        if l.strip():
            print("    %s" % l.strip())
    print("    код %d" % p.returncode)
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
