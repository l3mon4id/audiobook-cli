# Audiobook CLI
Python CLI toolset for the use with audiobooks. Current feature set:

- Merge mp3 files into m4a/m4b and keep timestamps as chapters
- Grab metadata - including chapters - from audible
- Create paths based on metadata

> [!NOTE]
> This project is work in progress. The documentation is not complete, yet.

## Installation
Clone this repository and install audiobook-cli via `pip` - ideally using a virtual environment. This project requires python3.11 (3.12 is not supported by `audible`, yet). Afterwards you can access the cli via `abc` command.

## Functionality
### Audible
#### Login
```
abc audible -l <locale> -e <encryption password> login [--use-browser] [--username] [--password] [--opt]
```
- `--locale / -l`: Audible locale code 
- `--encryption / -e`: Encryption password for storing the audible session encrypted on the disk

- `--use-browser`: Uses the `audible` lib browser based login where you copy a link, login to audible via browser and copy the resulting link. This is the preferred way of logging in, but it needs a big terminal buffer.

OR

- `--username`
- `--password`
- `--otp`: Optionally one time password if 2fa is enabled.

### Merge mp3 files

```
abc merge-mp3 --output <path to output file> [--run|-r] [--chapterize|-c] "*.mp3"
```

- `--run`: Actually run the via ffmpeg. Without this command, the ffmpeg command will be displayed.
- `--chapterize`: Keep the timestamps from the mp3 files as chapters.
