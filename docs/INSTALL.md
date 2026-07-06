# Installation

## For Mac Users

If you downloaded the ZIP from GitHub Releases:

1. Unzip the file.
2. Open the unzipped `OrderAnalyzer` folder.
3. Double-click `start.command`.
4. If macOS blocks it, right-click `start.command` and choose `Open`.

The script will install dependencies and start the app.

## Terminal Commands

Open Terminal, then enter the unzipped project folder before running install commands.

Example:

```bash
cd ~/Downloads/OrderAnalyzer-0.3.2
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

If the folder name is different, replace `~/Downloads/OrderAnalyzer-0.3.2` with the real unzipped folder path.

## Common Error

If you see:

```text
ERROR: Could not open requirements file: No such file or directory: 'requirements.txt'
No module named streamlit
```

It means Terminal is not inside the project folder. Run `cd` into the unzipped OrderAnalyzer folder first, then run the commands again.
