# gitignore_dataset
Dataset for .gitignore Analysis

## TL; DR
This repository includes the dataset of .gitignore:
1. Unique .gitignore files (1999 files)
2. Raw repository data of 1 (1999 repositories)
2. *Restored* directory structures (992 repositories)
    - **Restoring** files based on .gitignore
    - Truncating contents of all files (except .gitignore)

# Unique .gitignore Files
1999 unique .gitignore files randomly collected from GitHub are provided in ``/ignores``.
Each file has a unique ID and is stored in a directory labeled by it.
Note that files are renamed "gitignore" (leading dot removed), so as not to work as real .gitignores.
**Please re-rename them when using it as real .gitignore.**

Total Size: 16 MB

## Raw Repository Data
Contents of 1999 GitHub repositories that contain .gitignore described earlier are provided in ``/raw_data``.
Each data is in ZIP format, named by .gitignore ID.

Total size: 5.4 GB

## *Restored* Directory Structures
856 *restored* directory structures of repositories are provided in ``/restored``.
All of the files included, except for .gitignore, are emptied for the sake of this repository size.

*Restoring* means making the directory structure what it **may** have been before .gitignore is applied.

Note that it may **not** be the same as what it was before ignoring.

Total size: 48 MB

## Other
``/download_out`` contains ``download_info.csv`` which shows repository information for each ID, and ``/restore_out`` contains ``restore_info.csv`` which shows each restoration information.

## Usage
Download ZIP (recommended, because there are too many files for Git to track.) or clone this repository.

## Building Your Own Dataset
You can build your own dataset by using the programs provided.
Run the commands below in the **root** directory of this repository.

0. Get your personal access token of GitHub and store it in ``./GITHUB_TOKEN`` for getting rid of GitHub API call limit.

1. Download raw repository data and save them in ``/raw_data`` with download.py:

    ```bash
    python download.py
    ```

    Downloading repository is randomly selected from ``ignores.csv`` (includes 5440229 .gitignores).

    You can set the number of repositories to be downloaded (default 10) and the maximum size of each repository (default 10 MB):

    ```bash
    # 1000 files, 50 MB
    python download.py 1000 50000   # set maximum size in KB
    ```

    You can extract .gitignore files from each repository data and save them in ``/ignores`` by running ``extract.sh``:

    ```bash
    bash extract.sh
    ```

2. Restore files with restore.py:

    ```bash
    python restore.py
    ```

    You can set the number of repositories to run restoration.
    If not set, all of the repositories in ``/raw_data`` are restored.
    You can also restore a certain repository by specifying its ID.

    ```bash
    python restore.py [-n NUM_FILES] [-f TARGET_ID]
    ```

    (Note that -n and -f flags are exclusive.)