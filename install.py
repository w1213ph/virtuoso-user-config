#!/usr/bin/env python3
"""Portable, opt-in Virtuoso configuration installer. Python 3.6+; stdlib only."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

SOURCE = Path(__file__).resolve().parent
BEGIN = b"; BEGIN VIRTUOSO-USER-CONFIG\n"
END = b"; END VIRTUOSO-USER-CONFIG\n"
FIELDS = ("id", "vgs", "vds", "vth", "gm", "region", "gmoverid", "rout", "ron", "cgg")
FEATURES = ("ciw", "form-fonts", "labels", "viva", "q-scope", "undo-history", "ade-ui",
            "op-annotations", "ade-models", "workspace")
RECOMMENDED = FEATURES[:7]


def selected_features(args):
    value = getattr(args, "features", "recommended")
    selected = set(RECOMMENDED if value == "recommended" else FEATURES if value == "all"
                   else filter(None, value.split(",")))
    if getattr(args, "op", False):
        selected.add("op-annotations")
    if args.models:
        selected.add("ade-models")
    if args.workspace_template:
        selected.add("workspace")
    if selected - set(FEATURES):
        raise ValueError("Unknown features: " + ",".join(sorted(selected - set(FEATURES))))
    if not selected:
        raise ValueError("Select at least one feature")
    if "ade-models" in selected and not args.models:
        raise ValueError("ade-models requires --models with a local model map")
    if "workspace" in selected and not args.workspace_template:
        raise ValueError("workspace requires --workspace-template from the local installation")
    return [name for name in FEATURES if name in selected]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def quote(value):
    if any(ord(c) < 32 for c in str(value)):
        raise ValueError("Control characters are not allowed in SKILL strings")
    return json.dumps(str(value), ensure_ascii=True)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def annotations(devices, active=False):
    """Generate native Annotation Setup data, without reading/copying PDK code."""
    entries = []
    seen = set()
    for item in devices:
        lib, cell = item["library"], item["cell"]
        slots = item.get("inline_slots", 5)
        if not all(isinstance(v, str) and re.fullmatch(r"[A-Za-z0-9_.+-]+", v)
                   for v in (lib, cell)):
            raise ValueError("Library/cell names must be simple identifiers")
        if type(slots) is not int or not 0 <= slots <= 5:
            raise ValueError("inline_slots must be an integer from 0 to 5")
        if (lib, cell) in seen:
            raise ValueError("Duplicate annotation device")
        seen.add((lib, cell))
        entries.append((lib, cell, slots))
    if not entries:
        raise ValueError("Annotation device list must not be empty")
    lines = ["Design:configTest mos_probe schematic",
             "annInstExceptionList:" + ",".join("%s %s *" % (a, b) for a, b, _ in entries), ""]
    for lib, cell, slots in entries:
        lines += ["Instance:%s %s *" % (lib, cell), "cdsParam:"]
        for i, field in enumerate(FIELDS, 1):
            visible = "true" if i <= slots else "false"
            lines += ["%d dbLabel :%s" % (i, visible),
                      "%d display mode:%s" % (i, "opPoint" if active else "parameter"),
                      "%d opPoint annotate?:%s" % (i, visible),
                      "%d opPoint balloon?:true" % i,
                      "%d opPoint displayType:DC" % i,
                      "%d opPoint label:%s" % (i, field)]
        lines.append("")
    return "\n".join(lines) + "\n"


def models(config):
    profiles = config["profiles"]
    if not profiles:
        raise ValueError("Model profiles must not be empty when --models is supplied")
    result, seen = [], set()
    for profile in profiles:
        tech = profile["technology_read_path"]
        if tech in seen or not Path(tech).is_absolute() or not Path(tech).is_dir():
            raise ValueError("Technology path must be unique, absolute and exist locally")
        seen.add(tech)
        rows = []
        for row in profile["models"]:
            path, section = row["file"], row.get("section", "")
            if not Path(path).is_absolute() or not Path(path).is_file():
                raise ValueError("Each model file must be absolute and exist locally")
            rows.append("list(%s %s)" % (quote(path), quote(section)))
        if not rows:
            raise ValueError("Each profile must contain at least one model")
        result.append(" list(%s list(%s))" % (quote(tech), " ".join(rows)))
    return "; Locally generated paths only; no model contents.\nvucAmModelProfiles=list(\n%s\n)\n" % "\n".join(result)


def render(args):
    root = Path(args.root).expanduser().absolute()
    root_string = root.as_posix()
    files = {}
    features = selected_features(args)
    env = "; Generated from selected modules: %s\n" % ",".join(features)
    for feature in features:
        module = SOURCE / ("features/" + feature + ".cdsenv")
        if module.exists():
            env += module.read_text(encoding="utf-8") + "\n"
    if "op-annotations" in features:
        devices = read_json(args.devices or SOURCE / "examples/devices.analoglib.json")
        files["op-annotation/dc-op-annotations.as"] = annotations(devices).encode()
        files["op-annotation/dc-op-active.as"] = annotations(devices, True).encode()
        files["op-annotation/mode-switch.il"] = (SOURCE / "skill/mode-switch.il.in").read_text(
            encoding="utf-8").replace("@ROOT@", quote(root_string)).encode()
        env += '\nauCore.misc annotationSetupFileList string %s\n' % quote(
            root_string + "/op-annotation/dc-op-annotations.as")
    if args.models:
        files["ade-models/profiles.il"] = models(read_json(args.models)).encode()
        files["ade-models/auto-models.il"] = (SOURCE / "skill/auto-models.il.in").read_text(
            encoding="utf-8").replace("@ROOT@", quote(root_string)).encode()
    loader = (SOURCE / "skill/ui.il.in").read_text(encoding="utf-8")
    loader = loader.replace("@ROOT@", quote(root_string)).replace("@OP@", "t" if "op-annotations" in features else "nil")
    loader = loader.replace("@MODELS@", "t" if args.models else "nil")
    loader = loader.replace("@FEATURES@", "list(%s)" % " ".join(quote(name) for name in features))
    fonts = []
    if "ciw" in features:
        fonts.append('hiSetFont("ciw" ?name "mono" ?size 18 ?bold nil ?italic nil)')
    if "form-fonts" in features:
        fonts += ['hiSetFont("label" ?size 11 ?bold nil ?italic nil)',
                  'hiSetFont("text" ?size 11 ?bold nil ?italic nil)']
    loader = loader.replace("@FONTS@", "\n".join(fonts))
    files["ui.il"], files["ui.cdsenv"] = loader.encode(), env.encode()
    verify = (SOURCE / "skill/verify-header.il").read_text(encoding="utf-8")
    for line in env.splitlines():
        parts = line.split(None, 3)
        if not line.startswith(";") and len(parts) == 4:
            verify += 'vucAssert(envGetVal(%s %s) %s %s)\n' % (
                quote(parts[0]), quote(parts[1]), parts[3], quote(parts[0] + "/" + parts[1]))
    if "op-annotations" in features:
        verify += 'vucAssert(boundp(\'vucOpModeSwitchLoaded) && vucOpModeSwitchLoaded t "DC menu hook loaded")\n'
    if "ade-models" in features:
        verify += 'vucAssert(length(vucAmModelProfiles) %d "local model profiles loaded")\n' % len(read_json(args.models)["profiles"])
        verify += 'vucAssert(envGetVal("asimenv.startup" "sessInitTrigFunc") "vucAmSessionInit" "ADE hook registered")\n'
    verify += 'printf("VUC_VERIFICATION_FAILURES=%d\\n" vucVerificationFailures)\n'
    files["verify.il"] = verify.encode()
    writes = {root / key: value for key, value in files.items()}
    identity = digest(root_string.encode())[:12].encode()
    begin = BEGIN.rstrip() + b" " + identity + b"\n"
    end = END.rstrip() + b" " + identity + b"\n"
    block = begin + ("; VUC FEATURES %s\n" % ",".join(features)).encode() + (
        'unless(errset(load(%s) t)\n warn("[user-config] Load failed; check CIW.\\n")\n)\n' %
        quote(root_string + "/ui.il")).encode() + end
    entries = args.cdsinit or [str(Path.home() / ".cdsinit")]
    for entry in entries:
        path = Path(entry).expanduser().absolute()
        if path in writes or path == root / ".install.json" or root in path.parents:
            raise ValueError("Each .cdsinit must be unique and outside the installation root")
        if path.is_symlink() or not path.parent.is_dir():
            raise ValueError(".cdsinit must have an existing parent and must not be a symlink")
        old = path.read_bytes() if path.exists() else b""
        if begin in old:
            raise ValueError("A managed startup block already exists; use status/rollback first")
        for group in re.findall(rb"^; VUC FEATURES ([a-z,-]+)\r?$", old, re.M):
            if set(group.decode().split(",")) & set(features):
                raise ValueError("Selected features overlap an existing module in this .cdsinit")
        writes[path] = old + (b"\n" if old and not old.endswith(b"\n") else b"") + block
    if args.workspace_template:
        template = Path(args.workspace_template).expanduser().read_bytes()
        if not template.startswith(b"WCfg"):
            raise ValueError("Workspace template must be a native WCfg workspace file")
        directory = Path.home() / ".cadence/dfII/workspaces/Schematics"
        path = directory / "Design_Default.workspace"
        if path.exists() or path.is_symlink():
            raise ValueError("Design_Default.workspace already exists; refusing to overwrite")
        writes[path] = template
        writes[directory / "workspace.default"] = b"Design_Default\n"
    for path in writes:
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError("Refusing symlink or non-file target: %s" % path)
    return root, writes


def write_atomic(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".vuc-tmp")
    # Exclusive create: never follow a pre-existing temporary-file symlink.
    with temp.open("xb") as handle:
        handle.write(data)
    try:
        os.chmod(str(temp), mode)
        os.replace(str(temp), str(path))
    finally:
        if temp.exists():
            temp.unlink()


def install(args):
    root, writes = render(args)
    if root.is_symlink() or (root.exists() and any(root.iterdir())):
        raise ValueError("Installation root must be new or empty; use a separate test root")
    manifest = {"version": 1, "status": "prepared", "files": []}
    for path, data in writes.items():
        before = path.read_bytes() if path.exists() else None
        manifest["files"].append({"path": str(path), "installed_sha256": digest(data),
                                  "before": None if before is None else base64.b64encode(before).decode("ascii"),
                                  "startup_suffix": base64.b64encode(data[len(before or b""):]).decode("ascii")
                                      if root not in path.parents and data.endswith(END.rstrip() + b" " + digest(root.as_posix().encode())[:12].encode() + b"\n") else None,
                                  "mode": stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600})
    root.mkdir(parents=True, exist_ok=True)
    state = root / ".install.json"
    write_atomic(state, json.dumps(manifest, indent=2).encode())
    done = []
    try:
        for item in manifest["files"]:
            path = Path(item["path"])
            # Detect edits between preflight and installation.
            original = None if item["before"] is None else base64.b64decode(item["before"])
            if (path.read_bytes() if path.exists() else None) != original:
                raise ValueError("Target changed during install: %s" % path)
            write_atomic(path, writes[path], item["mode"])
            done.append(item)
        manifest["status"] = "installed"
        write_atomic(state, json.dumps(manifest, indent=2).encode())
    except Exception:
        for item in reversed(done):
            restore(item)
        manifest["status"] = "install_failed_reverted"
        write_atomic(state, json.dumps(manifest, indent=2).encode())
        raise
    print("Installed. Existing Virtuoso sessions are untouched. Start a new session to validate.")
    print("Rollback: python3 install.py rollback --root %s" % quote(root.as_posix()))


def restore(item):
    path = Path(item["path"])
    if item.get("startup_suffix") and digest(path.read_bytes()) != item["installed_sha256"]:
        suffix = base64.b64decode(item["startup_suffix"])
        remaining = path.read_bytes().replace(suffix, b"", 1)
        if remaining or item["before"] is not None:
            write_atomic(path, remaining, item["mode"])
        else:
            path.unlink()
        return
    if item["before"] is None:
        path.unlink()
    else:
        write_atomic(path, base64.b64decode(item["before"]), item["mode"])


def state_action(args):
    state = Path(args.root).expanduser().absolute() / ".install.json"
    manifest = read_json(state)
    if manifest["status"] != "installed":
        raise ValueError("Installation is not active: %s" % manifest["status"])
    conflicts = []
    for item in manifest["files"]:
        path = Path(item["path"])
        if path.is_symlink() or not path.is_file():
            conflicts.append(str(path))
            continue
        current = path.read_bytes()
        if item.get("startup_suffix"):
            valid = current.count(base64.b64decode(item["startup_suffix"])) == 1
        else:
            valid = digest(current) == item["installed_sha256"]
        if not valid:
            conflicts.append(str(path))
    if conflicts:
        raise ValueError("Files changed since installation; no rollback writes made:\n" + "\n".join(conflicts))
    if args.command == "status":
        print("All %d managed files/blocks match; unrelated startup edits are preserved." % len(manifest["files"]))
        return
    for item in reversed(manifest["files"]):
        restore(item)
    manifest["status"] = "rolled_back"
    write_atomic(state, json.dumps(manifest, indent=2).encode())
    print("Rolled back. Backup manifest retained; running sessions were not changed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "install", "status", "rollback"))
    parser.add_argument("--root", default=str(Path.home() / ".cadence/virtuoso-user-config"))
    parser.add_argument("--cdsinit", action="append", help="Repeat for each actual startup file")
    parser.add_argument("--features", default="recommended", help="Comma-separated independent modules, recommended, or all")
    parser.add_argument("--op", action="store_true", help="Enable optional DC annotation/menu compatibility")
    parser.add_argument("--devices", help="Local JSON device list for op-annotations")
    parser.add_argument("--models", help="Local JSON model map; activates new-session hook")
    parser.add_argument("--workspace-template", help="Local installed Basic.workspace; optional")
    args = parser.parse_args()
    try:
        if args.devices and "op-annotations" not in selected_features(args):
            raise ValueError("--devices requires op-annotations or --op")
        if args.command in ("status", "rollback"):
            state_action(args)
        elif args.command == "install":
            install(args)
        else:
            root, writes = render(args)
            for path, data in writes.items():
                print("%s  %d bytes  %s" % (digest(data), len(data), path))
            print("Plan only; no files written. Root: %s" % root)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print("ERROR: %s" % error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
