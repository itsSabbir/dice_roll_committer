# 🎲 Dice Roll Committer

A time-based probabilistic commit automation system powered by Python and GitHub Actions.  
This repository houses a fully autonomous bot that decides, based on the current UTC hour and a pseudo-random roll, whether to commit a timestamped log to the repository every hour.

---

## 📌 Overview

This project combines randomness with temporal conditions to create a deterministic-yet-unpredictable commit pattern. The system is built using:

- A Python script to encapsulate commit logic
- A GitHub Actions workflow to schedule execution every hour
- Git versioning and CI best practices to ensure consistency and reliability

---

## ⚙️ How It Works

Every hour on the hour, GitHub Actions triggers a Python script. The script:

1. **Reads the current UTC hour**
2. **Decides whether to commit using this logic:**
   - **Special Hours (multiples of 3 including 0):** Commit always (100% chance)
   - **Even Hours (non-multiples of 3):** 50% chance to commit
   - **Odd Hours (non-multiples of 3):** 25% chance to commit
3. **If committing:** Appends a short log with a timestamp and the reason to `dice_roll_log.txt`
4. **If not committing:** Exits cleanly without modifying the file

The GitHub Actions workflow then detects file changes and commits if necessary.

---

## 📁 Repository Structure

```

/
├── .github/
│   └── workflows/
│       └── dice\_roll\_commit.yml     # GitHub Actions workflow configuration
├── dice\_roll\_committer.py           # Python script handling commit logic
├── dice\_roll\_log.txt                # Log file with commit history
├── README.md                        # Project documentation
└── .gitignore                       # Python .gitignore template

```

---

## 🚀 Automation Logic Details

### 🎯 Decision Strategy (inside `dice_roll_committer.py`)

| Hour Type         | Condition                  | Commit Probability |
|------------------|----------------------------|---------------------|
| Special Hour      | `hour % 3 == 0`             | 100% (guaranteed)   |
| Even Hour         | `hour % 2 == 0 && hour % 3 != 0` | 50%                  |
| Odd Hour          | `hour % 2 != 0 && hour % 3 != 0` | 25%                  |

The script outputs logs explaining the decision-making path, including the random value rolled and its outcome.

### 🧪 Exit Codes

The Python script uses exit codes to signal outcome:

- `0`: Commit recommended and file modified
- `1`: Error occurred during execution
- `2`: No commit recommended; file unchanged

---

## 🔄 GitHub Actions Workflow

### `.github/workflows/dice_roll_commit.yml`

- **Runs hourly via CRON schedule**: `'0 * * * *'`
- **Manages concurrency** to avoid overlapping runs
- **Pulls changes with rebase** before push to avoid conflicts
- **Attempts up to 3 Git pushes** if failures occur
- **Skips commit if file not changed** even when script exits `0`

The workflow is hardened for reliability, using explicit step evaluation and Git safeguards.

---

## ✅ Key Features

- ⌚ **Hourly execution** via GitHub Actions CRON
- 🎲 **Randomized logic** with time-awareness
- ✍️ **Minimal, traceable commits** for clean history
- 🧪 **Robust error handling** and process isolation
- ⚙️ **Environment-agnostic design** (runs on any Linux runner with Python 3.11+)

---

## 📈 Use Cases

- Fun and automated **GitHub contribution graphs**
- Experimenting with **automated workflows and time-based triggers**
- Learning **CI/CD principles** in a lightweight but structured environment
- A sandbox for **GitHub Actions, Python scripting, and Git automation**

---

## 📊 Sample Output (inside `dice_roll_log.txt`)

```

2025-05-21T00:00:01+00:00 - Commit triggered. Reason: Guaranteed commit: Current hour 0 UTC is a multiple of 3.
2025-05-21T03:00:02+00:00 - Commit triggered. Reason: Guaranteed commit: Current hour 3 UTC is a multiple of 3.
2025-05-21T06:00:03+00:00 - Commit triggered. Reason: Guaranteed commit: Current hour 6 UTC is a multiple of 3.

```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Contributing

Pull requests and ideas are welcome! If you have feature suggestions (e.g., day-based logic, multiple output files, webhook integration), feel free to open an issue or contribute a PR.

---

## 🔧 Requirements

- GitHub Actions environment (Ubuntu runner)
- Python 3.11+
- No external dependencies (standard library only)

---

## 🧠 Author

Developed and maintained by [Sabbir Hossain](https://github.com/itsSabbir).  
If you enjoy this project, give it a ⭐ and follow for more automations!


