\<div align="center"\>

# 🎲 Dice Roll Committer

### A Production-Ready, Probabilistic Git Committing Engine

[](https://www.google.com/search?q=https://github.com/itsSabbir/dice-roll-committer/actions/workflows/dice_roll_commit.yml)
[](https://opensource.org/licenses/MIT)
[](https://www.google.com/search?q=https://github.com/itsSabbir/dice-roll-committer/pulls)

A fully autonomous system that leverages Python and GitHub Actions to introduce repository activity based on a configurable, time-aware, probabilistic model.

\</div\>

-----

## 📖 Table of Contents

  - [📍 Overview](https://www.google.com/search?q=%23-overview)
  - [✨ Core Features](https://www.google.com/search?q=%23-core-features)
  - [🚀 Live Demo & Output](https://www.google.com/search?q=%23-live-demo--output)
  - [🏛️ Architecture and Process Flow](https://www.google.com/search?q=%23%EF%B8%8F-architecture-and-process-flow)
  - [📁 File Manifest](https://www.google.com/search?q=%23-file-manifest)
  - [▶️ Getting Started (Deployment)](https://www.google.com/search?q=%23%EF%B8%8F-getting-started-deployment)
  - [🔧 Configuration](https://www.google.com/search?q=%23-configuration)
  - [💻 Development and Local Testing](https://www.google.com/search?q=%23-development-and-local-testing)
  - [🤝 Contributing](https://www.google.com/search?q=%23-contributing)
  - [📜 License](https://www.google.com/search?q=%23-license)
  - [✍️ Author](https://www.google.com/search?q=%23%EF%B8%8F-author)

-----

## 📍 Overview

The Dice Roll Committer is an advanced automation tool designed to demonstrate robust CI/CD principles in a practical, engaging way. At the start of every hour, it triggers a workflow that executes a sophisticated Python script. This script acts as the "decision engine," determining whether to make a commit based on a set of rules combining UTC time and pseudo-random chance.

This project is more than a simple bot; it's a production-quality template for building resilient, configurable, and observable automations on the GitHub platform.

> **Core Philosophy: Separation of Concerns**
> The system is architected to cleanly separate responsibilities. The Python script handles the **what** (the decision-making logic), while the GitHub Actions workflow manages the **how** (the execution environment, error handling, Git operations, and reporting). This modularity makes the project easier to maintain, test, and extend.

## ✨ Core Features

  - **Autonomous Hourly Operation**: Runs automatically every hour via a CRON-based GitHub Actions schedule (`'0 * * * *'`). It is designed for true "set it and forget it" operation.
  - **Configurable Probabilistic Logic**: The entire decision engine is managed by a central `Config` class in the Python script. Easily change commit probabilities or switch to a 100% guaranteed commit mode without ever touching the workflow YAML.
  - **High-Reliability Execution**: The workflow is hardened against common failures. It uses `git pull --rebase` to prevent push conflicts and a robust loop that retries `git push` up to three times to handle transient network issues.
  - **Decoupled Architecture**: The script and workflow communicate via artifacts (`dice_roll_log.txt`, `commit_message.txt`) and exit codes. This "contract" means either component can be updated independently as long as the contract is honored.
  - **Rich, Structured Commits**: Generates detailed, multi-line commit messages using the Conventional Commits standard. This provides excellent, human-readable traceability for every automated action directly in the Git history.
  - **Superior Observability**: Every workflow run concludes with a **Job Summary**, a beautiful, human-readable report card posted directly to the Actions UI, detailing the outcome of the run with links and logs.
  - **Concurrency Management**: Prevents workflow pile-ups and race conditions using `concurrency.group`, ensuring only one instance runs at a time for any given branch.

## 🚀 Live Demo & Output

You can see the results of this automation live in this repository\!

  - **View All Workflow Runs**: [**Actions Tab**](https://www.google.com/search?q=https://github.com/itsSabbir/dice-roll-committer/actions/workflows/dice_roll_commit.yml)
  - **See the Resulting Commits**: [**Commit History**](https://www.google.com/search?q=https://github.com/itsSabbir/dice-roll-committer/commits/main)

### Job Summary Output

After each run, a detailed summary provides at-a-glance status information.

### Commit Message Example

Each commit is rich with context, explaining exactly why it was made.

```
chore(automated): Dice roll log update triggered at 2025-06-17T04:00:15+00:00 UTC.

Trigger Reason: Success on even hour 4 UTC.

### Details
- hour_utc: 4
- roll: 0.3142
- threshold: 0.5
- outcome: success
```

## 🏛️ Architecture and Process Flow

The system operates through a clear, orchestrated sequence of events. This diagram illustrates the interaction between the different components of the system.

```mermaid
graph TD
    A[GitHub Actions Scheduler] --triggers every hour--> B{Workflow Run};
    B --starts job--> C[1. Checkout Repository];
    C --code ready--> D[2. Setup Python];
    D --env ready--> E[3. Run dice_roll_committer.py];
    E --decision logic--> F{Decision Made};
    F --If NO (Exit 2)--> G[End Run Cleanly];
    F --If YES (Exit 0)--> H[Create/Update Files];
    subgraph "Python Script Artifacts"
        H --> I[dice_roll_log.txt];
        H --> J[commit_message.txt];
    end
    J --read by--> K[4. Evaluate & Prepare];
    K --if should_commit is true--> L[5. Commit & Push];
    L --pushes to--> M[Remote Repository];
    subgraph "Workflow Reports"
        G --> N[6. Generate Job Summary];
        L --on success/failure--> N;
    end
```

**Step-by-Step Breakdown:**

1.  **Trigger**: The `.github/workflows/dice_roll_commit.yml` workflow is triggered by the `schedule` CRON at the start of every hour.
2.  **Environment Setup**: The job runs on a fresh `ubuntu-latest` runner, checks out the repository code with full Git history (`fetch-depth: 0` is used to enable rebasing), and installs the specified Python version.
3.  **Decision Engine**: `dice_roll_committer.py` is executed. This script contains all the business logic. It evaluates the time and probabilities defined in its `Config` class and exits with a specific code to communicate its intent: `0` for commit, `2` for no commit.
4.  **Artifact Generation**: If a commit is decided, the Python script performs two critical actions: it appends a new entry to `dice_roll_log.txt` and writes a complete, formatted commit message into a temporary `commit_message.txt` file.
5.  **Workflow Evaluation**: The workflow's next step intelligently inspects the script's exit code. If the code is `0`, it proceeds and reads the entire multi-line message from `commit_message.txt` into memory. If the code is anything else, it gracefully skips the commit steps.
6.  **Git Execution**: The final sequence of actions configures Git with the author's details, adds the changed files, and performs the commit using the exact message captured from the file. A `git pull --rebase` is performed before `git push` to prevent conflicts, and the push itself is wrapped in a retry loop.
7.  **Reporting**: Regardless of the outcome (commit, no commit, or failure), the final step runs to generate and post the Job Summary.

## 📁 File Manifest

| File / Directory | Purpose | Git Tracked? |
| :--- | :--- | :--- |
| **`.github/workflows/`** | Contains all GitHub Actions workflow files. | Yes |
| `dice_roll_commit.yml` | The primary YAML workflow file that orchestrates the entire process. | Yes |
| **`dice_roll_committer.py`** | The core Python script containing the decision-making logic and artifact generation. | Yes |
| **`dice_roll_log.txt`** | A persistent log file that accumulates a history of every commit made by the script. | Yes |
| **`commit_message.txt`** | A temporary file created by the Python script on successful runs. It holds the next commit's message and is overwritten each time. It is then deleted by Git upon commit. | No (`.gitignore`) |
| **`README.md`** | This documentation file. | Yes |
| **`.gitignore`** | Specifies intentionally untracked files to ignore, such as `commit_message.txt`. | Yes |
| **`LICENSE`** | The project's MIT License file. | Yes |

## ▶️ Getting Started (Deployment)

You can deploy this system on your own repository in minutes.

1.  **Copy the Files**: Copy the `.github` directory, `dice_roll_committer.py`, `.gitignore`, and `LICENSE` to your own repository.

2.  **Configure Author Details**: Open `.github/workflows/dice_roll_commit.yml` and modify the `env` block with your own Git author name and email. The email should be one associated with your GitHub account to ensure contributions are linked correctly.

    ```yaml
    env:
      PYTHON_VERSION: '3.11'
      GIT_AUTHOR_NAME: "Your Name"         # <-- CHANGE THIS
      GIT_AUTHOR_EMAIL: "your-email@users.noreply.github.com" # <-- CHANGE THIS
      # ...
    ```

3.  **Commit & Push**: Commit the new files to your repository's main branch and push them to GitHub.

That's it\! The automation is now live. The workflow will trigger automatically at the top of the next hour.

## 🔧 Configuration

The behavior of the dice roller is controlled entirely within the `Config` class at the top of `dice_roll_committer.py`.

```python
# Example of how to change the configuration in dice_roll_committer.py

class Config:
    """Holds all configuration variables for the script."""
    # --- File Configuration ---
    LOG_FILENAME: str = "dice_roll_log.txt"
    COMMIT_MSG_FILENAME: str = "commit_message.txt"

    # --- Behavior Configuration ---
    # To guarantee a commit every hour, change this to True.
    GUARANTEE_COMMIT: bool = True #<-- EXAMPLE CHANGE

    # To make commits less likely, lower these values.
    PROBABILITIES: Dict[str, float] = {
        "even_hour": 0.10,  # 10% chance on even hours <-- EXAMPLE CHANGE
        "odd_hour": 0.05,   # 5% chance on odd hours  <-- EXAMPLE CHANGE
    }
    # ...
```

## 💻 Development and Local Testing

You can easily test changes before pushing them to your main branch.

  - **Cloud Testing (Manual Run)**: Push your changes to a development branch and trigger the workflow manually using the `workflow_dispatch` event in your repository's "Actions" tab. This allows you to test the full end-to-end process in a real GitHub Actions environment.

  - **Local Testing**: Run the Python script directly on your local machine to verify its decision logic and artifact generation.

    ```bash
    # Navigate to the repository root in your terminal
    python dice_roll_committer.py
    ```

    After running, check your local directory. If the script decided to commit, you will find `dice_roll_log.txt` (with a new line) and `commit_message.txt`. You can inspect their contents to ensure your logic changes are working as expected.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome\! This project serves as an excellent template for robust automation, and improvements are always encouraged. Please feel free to check the [issues page](https://www.google.com/search?q=https://github.com/itsSabbir/dice-roll-committer/issues).

## 📜 License

This project is distributed under the MIT License. See the `LICENSE` file for more information.

## ✍️ Author

**Sabbir Hossain** - [GitHub](https://github.com/itsSabbir) - *Initial work & maintenance*
