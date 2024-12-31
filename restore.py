import os
import sys
import subprocess
import random
from pathlib import Path
import time
import pandas as pd
import signal


def parse_args(argv):
    num_files = None
    target_id = None

    if "-n" in argv:
        idx = argv.index("-n")
        if idx + 1 < len(argv):
            num_files = int(argv[idx + 1])
        else:
            print(
                "Usage: python restore.py [-n NUM_FILES] [-f TARGET_ID] (-n and -f are exclusive)"
            )
            sys.exit(1)

    if "-f" in argv:
        idx = argv.index("-f")
        if idx + 1 < len(argv):
            target_id = argv[idx + 1]
        else:
            print(
                "Usage: python restore.py [-n NUM_FILES] [-f TARGET_ID] (-n and -f are exclusive)"
            )
            sys.exit(1)

    if num_files and target_id:
        print("Error: -n and -f cannot be used together")
        sys.exit(1)

    return num_files, target_id


def range_expand(pat: str) -> list[str]:
    def cat(l, rg, r):
        res = []
        chars = []
        i = 0
        while i < len(rg):
            if rg[i] == "-":
                chars.extend(chr(x) for x in range(ord(rg[i - 1]), ord(rg[i + 1]) + 1))
                rg = rg[: i - 1] + rg[i + 2 :]
                i -= 2
            i += 1
        chars.extend(rg)
        chars = set(chars)
        for c in chars:
            res.append(l + c + r)
        return set(res)

    res = cat(
        pat[: pat.index("[")],
        pat[pat.index("[") + 1 : pat.index("]")],
        pat[pat.index("]") + 1 :],
    )
    while True:
        tmp = set()
        for p in res.copy():
            if "[" in p and "]" in p:
                res.remove(p)
                tmp |= cat(
                    p[: p.index("[")],
                    p[p.index("[") + 1 : p.index("]")],
                    p[p.index("]") + 1 :],
                )
        if not tmp:
            break
        res |= tmp
    return list(res)


def concat_path(left, right):
    return f"{left}/{right}".replace("./", "").replace("//", "/").rstrip("/")


def restore(data_id):
    global_pat, global_count, globstar_pat, globstar_count, normal_pat, normal_count = (
        0,
        0,
        0,
        0,
        0,
        0,
    )
    flag = False
    for pathname, dirnames, filenames in os.walk("restored/tmp"):
        for filename in filenames:
            if filename == ".gitignore":
                if flag:
                    print("Multiple .gitignore files found. Skipping...")
                    return (), "fail_gitignore_placement"
                flag = True
                if pathname != f"restored/tmp/{data_id}":
                    print(".gitignore needs to be in the root directory. Skipping...")
                    return (), "fail_gitignore_placement"
                with open(concat_path(pathname, filename), "r") as file:
                    lines = file.read().splitlines()

                    # check if the file is valid in terms of grammar, the number of global patterns
                    nogp = 0
                    for pat in lines:
                        valid = os.system(
                            f"refactorign -p {concat_path(pathname, filename)} --validate 1>/dev/null 2>/dev/null"
                        )
                        if valid != 0:
                            print(
                                f"Invalid pattern found in {concat_path(pathname, filename)}. Skipping..."
                            )
                            return (), "fail_invalid_pattern"
                        pat = pat.rstrip("/")
                        if not "/" in pat:
                            nogp += 1
                        if nogp > 20 or len(dirnames) * (pow(2, nogp) - 1) > 2000000:
                            print("Too many directories to add. Skipping...")
                            return (), "fail_too_many_directories"
                    print("Valid .gitignore file found.")

                    for pat in reversed(lines):  # restore in reverse order
                        if "#" in pat or "!" in pat or pat == "" or pat == "/":
                            continue
                        pat = pat.rstrip("/")
                        if not "/" in pat or pat.startswith("**/"):  # global pattern
                            global_pat += 1
                            if pat.startswith("**/"):
                                pat = pat[3:]
                            for pathname2, dirnames2, filenames2 in os.walk(pathname):
                                files = map(
                                    lambda x: x.replace("\\", ""),  # remove escape
                                    (
                                        range_expand(pat)
                                        if "[" in pat
                                        and "]" in pat
                                        and not "\\[" in pat
                                        else [pat]
                                    ),
                                )
                                for adding_file in files:
                                    adding_file_path = concat_path(
                                        pathname2, adding_file
                                    )
                                    try:
                                        if not os.path.exists(adding_file_path):
                                            os.makedirs(adding_file_path)
                                            global_count += 1
                                    except:
                                        os.system(f"rm -rf restored/tmp/{data_id}")
                                        print(
                                            f"Global: Failed to add {adding_file_path}. Skipping..."
                                        )
                                        return (), "fail_other"
                        else:  # globstar / normal pattern
                            parts = [[x] for x in Path(pat).parts]
                            for i, part in enumerate(parts):
                                if (
                                    "[" in part[0]
                                    and "]" in part[0]
                                    and not "\\[" in part[0]
                                ):
                                    parts[i] = range_expand(part[0])
                            paths = [""]
                            for i, part in enumerate(parts):
                                tmp = []
                                for path in paths:
                                    for p in part:
                                        tmp.append(
                                            f"{path}{p}{'/' if i < len(parts) - 1 else ''}"
                                        )
                                paths = tmp
                            for path in paths:
                                path = path.rstrip("/")
                                # globstar handling
                                # this program does not consider the case where the globstar appears more than once
                                if path.endswith("/**"):
                                    globstar_pat += 1
                                    root = concat_path(
                                        pathname, path.removesuffix("/**")
                                    )
                                    for (
                                        pathname3,
                                        dirnames3,
                                        filenames3,
                                    ) in os.walk(root):
                                        dir_path = concat_path(pathname3, "**")
                                        try:
                                            if not os.path.exists(dir_path):
                                                os.makedirs(dir_path)
                                                globstar_count += 1
                                        except:
                                            os.system(f"rm -rf restored/tmp/{data_id}")
                                            print(
                                                f"Trailing globstar: Failed to add {dir_path}. Skipping..."
                                            )
                                            return (), "fail_other"
                                elif "/**/" in path:
                                    globstar_pat += 1
                                    idx = path.index("/**/")
                                    base, target = path[:idx], path[idx + 4 :]
                                    root = concat_path(pathname, base)
                                    for (
                                        pathname3,
                                        dirnames3,
                                        filenames3,
                                    ) in os.walk(root):
                                        dir_path = concat_path(pathname3, target)
                                        try:
                                            if not os.path.exists(dir_path):
                                                os.makedirs(dir_path)
                                                globstar_count += 1
                                        except:
                                            os.system(f"rm -rf restored/tmp/{data_id}")
                                            print(
                                                f"Middle globstar: Failed to add {dir_path}. Skipping..."
                                            )
                                            return (), "fail_other"
                                else:  # normal pattern
                                    normal_pat += 1
                                    dir_path = concat_path(pathname, path)
                                    try:
                                        if not os.path.exists(dir_path):
                                            os.makedirs(dir_path)
                                            normal_count += 1
                                    except:
                                        os.system(f"rm -rf restored/tmp/{data_id}")
                                        print(
                                            f"Normal: Failed to add {dir_path}. Skipping..."
                                        )
                                        return (), "fail_other"
                    print("File restoration completed.")
            else:
                other = concat_path(pathname, filename)
                if os.path.islink(other):
                    continue
                try:
                    with open(other, "w") as file:
                        file.truncate(0)
                        file.close()
                except:
                    print(f"Failed to truncate {other} .")
    return (
        global_pat,
        global_count,
        globstar_pat,
        globstar_count,
        normal_pat,
        normal_count,
    ), None


class TimeoutError(Exception):
    pass


def timeout_handler():
    raise TimeoutError()


def run_with_timeout(timeout, func, *args, **kwargs):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    try:
        return func(*args, **kwargs)
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    if not os.path.isfile(os.path.join(os.getcwd(), "restore.py")):
        print("Please run this script from the root directory of gitignore_dataset.")
        sys.exit(1)

    if not os.path.exists("raw_data"):
        print("No raw_data directory found. Download the raw data first.")
        sys.exit(1)

    NUM_FILES, TARGET_ID = parse_args(sys.argv)

    if os.path.exists("restored"):
        os.system(
            'echo -n "Removing existing restored data directory... " && rm -rf restored && echo "OK."'
        )
    os.makedirs("restored")

    data_list = os.listdir("raw_data") if TARGET_ID is None else [f"{TARGET_ID}.zip"]
    random.shuffle(data_list)

    success = 0
    rels: list[dict] = []
    log = {
        "total": 0,
        "success": 0,
        "fail_invalid_pattern": 0,
        "fail_too_many_directories": 0,
        "fail_gitignore_placement": 0,
        "fail_other": 0,
    }

    for raw_data in data_list:
        data_id = raw_data.removesuffix(".zip")
        if not NUM_FILES is None and success >= NUM_FILES:
            break
        log["total"] += 1
        print("-" * 80)
        try:
            os.makedirs(f"restored/tmp/{data_id}")

            def unzip():
                subprocess.run(
                    [
                        "unzip",
                        "-qq",
                        f"raw_data/{raw_data}",
                        "-d",
                        f"restored/tmp/{data_id}",
                    ],
                    check=True,
                )

            run_with_timeout(
                10,
                unzip,
            )
        except:
            os.system(f"rm -rf restored/tmp/{data_id}")
            print(f"Failed or time-out to unzip {raw_data}. Skipping...")
            log["fail_other"] += 1
            continue
        start = time.perf_counter()
        result, fail = restore(data_id)
        end = time.perf_counter()
        if len(result) == 0:
            os.system(f"rm -rf restored/tmp/{data_id}")
            log[fail] += 1
            continue
        (
            global_pat,
            global_count,
            globstar_pat,
            globstar_count,
            normal_pat,
            normal_count,
        ) = result
        try:
            subprocess.run(
                ["mv", f"restored/tmp/{data_id}", "restored/"],
                check=True,
            )
            success += 1
            print(f"Restored {raw_data} .")
        except:
            print(f"An error occurred. Skipping...")
            os.system(f"rm -rf restored/tmp/{data_id}")
            log["fail_other"] += 1
            continue
        try:
            output_path = os.path.abspath(f"./restored/{data_id}.zip")
            subprocess.run(
                [
                    "zip",
                    "-qr",
                    output_path,
                    f".",
                ],
                cwd=f"./restored/{data_id}",
                check=True,
            )
            os.system(f"rm -rf restored/{data_id}")
        except:
            print(f"Failed to zip {raw_data}. Deleting...")
            os.system(f"rm -rf restored/{data_id}")
            log["fail_other"] += 1
            continue
        rels.append(
            {
                "number": int(data_id),
                "global_patterns": global_pat,
                "added_global": global_count,
                "globstar_patterns": globstar_pat,
                "added_globstar": globstar_count,
                "normal_patterns": normal_pat,
                "added_normal": normal_count,
                "time (sec)": round(end - start, 2),
            }
        )

    os.system("rm -rf restored/tmp")

    print("-" * 80)

    if os.path.exists("restore_out"):
        subprocess.run(["rm", "-rf", "restore_out"], check=True)
    os.makedirs("restore_out")
    pd.DataFrame(sorted(rels, key=lambda x: x["number"])).to_csv(
        "./restore_out/restore_info.csv", index=False
    )
    log["success"] = success
    pd.DataFrame([log]).to_csv("./restore_out/restore_log.csv", index=False)
    print("Saved restore information and log to restore_out.")

    print(f"Finished restoring {success} files.")
    os.system(r'echo "Total Size: \c" & du -sh restored | cut -f 1')
