# gitignore_dataset
GitHub Dataset for .gitignore Analysis

## TL; DR
This repository includes the dataset of GitHub repositories:
1. ZIP files of 1000 GitHub repositories
2. *Original* directory structures of 1 (941 / 1000 repos)
    - Truncated contents of all files (exc. .gitignore)
    - **Restored** files based on .gitignore

## ZIP Files
Randomly chosen 1000 GitHub repositories are provided as compressed ZIP files, up to 300 MB. Files over 50MB are stored with Git LFS.

Total size: 5.4 GB

## *Original* Directory Structures
*Original* directory structures of repositories of 1 are provided. Currently 941 out of 1000 repositories are available, which leaves much to be desired. All of the files included, except for .gitignore, are empty for the sake of this repository size.

The word *original* means that the directory structure is what it **may** have been before .gitignore is applied. In other words, files that are ignored by .gitignore are **restored** in the *original* directory structure. For this reason, .gitignores in them are renamed "gitignore", so as not to work as real .gitignores. **Please re-rename them when using.**

Note that it may **not** be the same as what it was before ignoring, though it is sure that applying .gitignore to it gives what is in the original ZIP file.

Total size: 1.8 GB

## Usage
Download ZIP (recommended, because there are too many files for Git to track.) or clone this repository.

## Building Your Own Dataset
You can build your own dataset by using the programs provided. Run the commands below in the **root** directory of this repository.

0. Get your personal access token of GitHub and store it in ``./GITHUB_TOKEN`` for getting rid of GitHub API call limit.

1. Download raw repository data with download.py:

    ```bash
    python download.py
    ```

    You can set the number of files to be downloaded (default 10) and the maximum size of each file (default 10 MB):

    ```bash
    # 1000 files, 50 MB
    python download.py 1000 50000   # set maximum size in KB
    ```

2. Restore files with restore.py:

    ```bash
    python restore.py
    ```

    (Restoring files without downloading raw data is not yet supported, but will be.)