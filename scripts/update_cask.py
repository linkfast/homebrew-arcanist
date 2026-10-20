"""Writes Casks/arcanist.rb for the newest Arcanist release with macOS disk images (pre-releases included, as long as
Arcanist only has those). Run by .github/workflows/update.yml; locally: python scripts/update_cask.py

Prints the version, and whether the cask changed (`changed=true|false` to $GITHUB_OUTPUT too).
"""
import hashlib
import json
import os
import pathlib
import re
import urllib.request

REPOSITORY = "linkfast/arcanist"
ROOT = pathlib.Path(__file__).resolve().parent.parent
CASK = ROOT / "Casks" / "arcanist.rb"
SEMVER = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$")


def get(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "homebrew-arcanist"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
        return response.read()


def precedence(tag):
    """SemVer 2.0 order: a release sorts after its pre-releases."""
    major, minor, patch, pre = SEMVER.match(tag).groups()
    if pre is None:
        return int(major), int(minor), int(patch), (1,)
    parts = tuple((0, int(p), "") if p.isdigit() else (1, 0, p) for p in pre.split("."))
    return int(major), int(minor), int(patch), (0, parts)


def sha256(asset):
    digest = asset.get("digest") or ""
    if digest.startswith("sha256:"):
        return digest.removeprefix("sha256:")
    return hashlib.sha256(get(asset["browser_download_url"])).hexdigest()


def newest():
    releases = json.loads(get(f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=30"))
    found = []
    for release in releases:
        tag = release["tag_name"]
        if release["draft"] or not SEMVER.match(tag):
            continue
        version = tag[1:]
        assets = {a["name"]: a for a in release["assets"]}
        images = {arch: assets.get(f"Arcanist-{version}-macos-{arch}.dmg") for arch in ("arm64", "x64")}
        if all(images.values()):
            found.append((precedence(tag), version, images))
    if not found:
        return None
    _, version, images = max(found, key=lambda f: f[0])
    return version, {arch: sha256(asset) for arch, asset in images.items()}


def cask(version, sums):
    return f'''cask "arcanist" do
  arch arm: "arm64", intel: "x64"

  version "{version}"
  sha256 arm:   "{sums["arm64"]}",
         intel: "{sums["x64"]}"

  url "https://github.com/linkfast/arcanist/releases/download/v#{{version}}/Arcanist-#{{version}}-macos-#{{arch}}.dmg"
  name "Arcanist"
  desc "Self-hosted music server"
  homepage "https://github.com/linkfast/arcanist"

  # Updated by this tap's workflow with every release; the app also updates itself (Velopack).
  livecheck do
    skip "Updated by the tap's workflow"
  end

  auto_updates true
  depends_on macos: ">= :sonoma"

  app "Arcanist.app"

  uninstall quit:      "net.linkfast.arcanist",
            launchctl: "net.linkfast.arcanist"

  zap trash: [
    "~/Library/Application Support/Arcanist",
    "~/Library/LaunchAgents/net.linkfast.arcanist.plist",
  ]

  caveats <<~EOS
    Arcanist.app runs from the menu bar and opens at login; the admin panel is at http://localhost:8484/admin.
    It is not notarized yet: the first time, confirm it in
    System Settings → Privacy & Security → Open Anyway.
  EOS
end
'''


def main():
    result = newest()
    changed = False
    if result is None:
        print("No release has macOS disk images yet.")
    else:
        version, sums = result
        text = cask(version, sums)
        changed = not CASK.exists() or CASK.read_text(encoding="utf-8") != text
        if changed:
            CASK.parent.mkdir(exist_ok=True)
            CASK.write_text(text, encoding="utf-8", newline="\n")
        print(f"Arcanist {version}: {'updated' if changed else 'already up to date'}")
    with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a", encoding="utf-8") as out:
        out.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    main()
