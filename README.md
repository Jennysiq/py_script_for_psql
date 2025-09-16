# Example script for Backup Restore
## Description: 
The script automatically launches PostgreSQL in Docker, restores the dump, extracts SSNs of users with status alive, and prints them to the console.
Tesult can be submitted back to the site.
---

## Dependencies

- Linux/macOS
- Docker
- Python 3.9+
- Python libs:

```bash
pip3 install -r requirements.txt
```
## Run Steps:
- Pull repo
- Rename .env.example -> .env
- export TOKEN var to env vars or in .env ``export TOKEN=token``
- Run python3 ./test.py

### P.S Tested in ubuntu WSL