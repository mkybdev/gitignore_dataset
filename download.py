import os
import random
import sys
import subprocess

import pandas as pd
import requests

if not os.path.isfile(os.path.join(os.getcwd(), "download.py")):
    print("Please run this script from the root directory of gitignore_dataset.")
    sys.exit(1)

args = sys.argv[1:]
if len(args) != 2:
    print("Usage: python download.py [NUM_FILES] [MAX_SIZE (KB)]")
    sys.exit(1)
NUM_FILES = int(args[0]) if args else 10
MAX_SIZE = int(args[1]) if args else 10000

try:
    if os.path.exists("raw_data"):
        subprocess.run(["rm", "-rf", "raw_data"], check=True)
    os.makedirs("raw_data", exist_ok=True)
except:
    print("Failed to remove/create raw_data directory. Exiting...")
    sys.exit(1)

try:
    print("Loading .gitignore file list...")
    df = pd.read_csv("ignores.csv")
    names = df["repo_name"].tolist()
    refs = df["ref"].tolist()
    paths = df["path"].tolist()
    print(f"Loaded {len(names)} file paths.")
except:
    print("Repository list (ignores.csv) is broken or not found.")

que = list(range(len(names)))
random.shuffle(que)
rels: list[dict] = []
log = {
    "total": 0,
    "success": 0,
    "fail_size": 0,
    "fail_download": 0,
    "fail_empty": 0,
    "fail_one_line": 0,
    "fail_template": 0,
    "fail_other": 0,
}

templates = []
for template in os.listdir("./templates"):
    with open(f"./templates/{template}") as f:
        templates.append(list(filter(lambda x: x != "", map(str.strip, f.readlines()))))


def is_template(lines):
    print("Checking if the file is a template...", end=" ")
    for template in templates:
        if abs(len(lines) - len(template)) > 1:
            continue
        diff = (
            set(lines) - set(template)
            if len(lines) > len(template)
            else set(template) - set(lines)
        )
        if len(diff) < 2:
            print(f"\n{repo}-{branch}/{path} is likely a template. Skipping...")
            return True
    print("OK.")
    return False


total = 0
success = 0
while success < NUM_FILES:
    if not que:
        print("No more repos to download.")
        break
    idx = que.pop()
    total += 1
    name, ref, path = names[idx], refs[idx], paths[idx]
    user, repo = name.split("/")
    branch = ref.split("/")[-1]
    print("-" * 80)
    url = f"https://api.github.com/repos/{user}/{repo}"
    TOKEN = open("GITHUB_TOKEN", "r").read().strip()
    r = requests.get(url=url, headers={"Authorization": f"Bearer {TOKEN}"})
    if r.status_code == 200:
        size = int(r.json()["size"])
        print(
            f"Got {url}, {size} KB. {"Downloading..." if size < MAX_SIZE else "Skipping..."}"
        )
        if size < MAX_SIZE:
            try:
                subprocess.run(
                    [
                        "wget",
                        "-q",
                        "--no-check-certificate",
                        f"https://github.com/{user}/{repo}/archive/{branch}.zip",
                        "-O",
                        f"./raw_data/{idx}.zip",
                    ],
                    check=True,
                )
                print(f"Downloaded {url} .")
            except:
                print(f"Failed to download {url}. Skipping...")
                subprocess.run([f"rm", "-rf", f"./raw_data/{idx}.zip"], check=True)
                log["fail_download"] += 1
                continue
            try:
                ignore = list(
                    map(
                        str.strip,
                        os.popen(
                            f'unzip -p -qq "./raw_data/{idx}.zip" "{repo}-{branch}/{path}"'
                        ).readlines(),
                    )
                )
                if len(ignore) == 0 or all(line == "" for line in ignore):
                    print(f"{repo}-{branch}/{path} is empty. Skipping...")
                    subprocess.run([f"rm", "-rf", f"./raw_data/{idx}.zip"], check=True)
                    log["fail_empty"] += 1
                    continue
                if len(ignore) == 1 or sum(line != "" for line in ignore) == 1:
                    print(f"{repo}-{branch}/{path} has only one line. Skipping...")
                    subprocess.run([f"rm", "-rf", f"./raw_data/{idx}.zip"], check=True)
                    log["fail_one_line"] += 1
                    continue
                if is_template(ignore):
                    subprocess.run([f"rm", "-rf", f"./raw_data/{idx}.zip"], check=True)
                    log["fail_template"] += 1
                    continue
            except:
                subprocess.run([f"rm", "-rf", f"./raw_data/{idx}.zip"], check=True)
                log["fail_other"] += 1
                continue
            try:
                subprocess.run(
                    [
                        "unzip",
                        "-qq",
                        f"./raw_data/{idx}.zip",
                        "-d",
                        f"./raw_data/{idx}_tmp",
                    ],
                    check=True,
                )
                subprocess.run(
                    [
                        "cp",
                        "-R",
                        f"./raw_data/{idx}_tmp/{repo}-{branch}/{path.removesuffix(".gitignore")}",
                        f"./raw_data/{idx}",
                    ],
                    check=True,
                )
                subprocess.run(
                    ["rm", "-rf", f"./raw_data/{idx}_tmp", f"./raw_data/{idx}.zip"],
                    check=True,
                )
                output_path = os.path.abspath(f"./raw_data/{idx}.zip")
                subprocess.run(
                    [
                        "zip",
                        "-qr",
                        output_path,
                        f".",
                    ],
                    cwd=f"./raw_data/{idx}",
                    check=True,
                )
                # subprocess.run(
                #     [
                #         "ls",
                #         "-a",
                #         f"./raw_data/{idx}",
                #     ]
                # )
                subprocess.run(["rm", "-rf", f"./raw_data/{idx}"], check=True)
            except:
                subprocess.run(
                    [
                        "rm",
                        "-rf",
                        f"./raw_data/{idx}_tmp",
                        f"./raw_data/{idx}.zip",
                        f"./raw_data/{idx}",
                    ],
                    check=True,
                )
                log["fail_other"] += 1
                continue
            success += 1
            rels.append(
                {
                    "number": idx,
                    "repo_name": name,
                    "ref": ref,
                    "path": path,
                    "size": size,
                }
            )
            print(f"Saved to {output_path} .")
        else:
            log["fail_size"] += 1
    else:
        print(f"Failed to get {url} .")

print("-" * 80)

if os.path.exists("download_out"):
    subprocess.run(["rm", "-rf", "download_out"], check=True)
os.makedirs("download_out")
pd.DataFrame(sorted(rels, key=lambda x: x["number"])).to_csv(
    "./download_out/download_info.csv", index=False
)
log["total"] = total
log["success"] = success
pd.DataFrame([log]).to_csv("./download_out/download_log.csv", index=False)
print("Saved downloaded files information and log to download_out.")

print(f"Downloaded {success} files. Run restore.py to extract the files.")
os.system(r'echo "Total Size: \c" & du -sh raw_data | cut -f 1')
