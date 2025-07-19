# dice_roll_committer.py
import datetime
import random
import os
import sys
import logging
from dataclasses import dataclass
from typing import Dict, Any

# ==================================================================================================
# --- CONFIGURATION CLASS: Centralizes all tunable parameters ---
# Best practice is to abstract configuration from application logic.
# This makes the script more maintainable, easier to test, and configurable
# without digging through function implementations.
# ==================================================================================================
class Config:
    """Holds all configuration variables for the script."""
    # --- File Configuration ---
    LOG_FILENAME: str = "dice_roll_log.txt"
    COMMIT_MSG_FILENAME: str = "commit_message.txt"

    # --- Behavior Configuration ---
    # Set to True to guarantee a commit every run, False for probabilistic commits.
    GUARANTEE_COMMIT: bool = False

    # Probabilities for dice rolls if GUARANTEE_COMMIT is False.
    # Encapsulating these in a dictionary makes the logic cleaner.
    PROBABILITIES: Dict[str, float] = {
        "even_hour": 0.50,  # 50% chance on even hours
        "odd_hour": 0.25,   # 25% chance on odd hours
    }

    # --- Git Commit Message Configuration ---
    # Using templates for commit messages ensures consistency.
    COMMIT_HEADER: str = "chore(automated):"
    COMMIT_BODY_TEMPLATE: str = "Dice roll log update triggered at {timestamp} UTC."
    COMMIT_REASON_TEMPLATE: str = "Trigger Reason: {reason}"

    # --- Logging Configuration ---
    LOG_LEVEL = logging.INFO
    # A detailed log format is crucial for debugging headless CI/CD runs.
    LOG_FORMAT: str = '%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'


# ==================================================================================================
# --- DATA CLASSES: For structured data transfer between functions ---
# Using dataclasses instead of tuples or dictionaries provides type safety and clarity.
# It's a clear, self-documenting way to define the 'shape' of data.
# ==================================================================================================
@dataclass
class CommitDecision:
    """Encapsulates the outcome of the commit decision logic."""
    should_commit: bool
    reason: str
    details: Dict[str, Any]  # For rich context like roll values, thresholds, etc.


# ==================================================================================================
# --- CORE LOGIC ---
# Functions are now more specialized and focused on a single responsibility.
# ==================================================================================================
def get_commit_decision() -> CommitDecision:
    """
    Determines if a commit should be made based on configured logic.

    This function encapsulates the "business logic" of the committer. It's
    decoupled from file I/O and system-level actions.

    Returns:
        CommitDecision: An object containing the decision, reason, and context.
    """
    # Always work in UTC for consistency in scheduled tasks.
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    current_hour_utc = now_utc.hour

    logging.info(f"Evaluating commit logic for UTC hour: {current_hour_utc}")

    # --- Guaranteed Commit Path ---
    if Config.GUARANTEE_COMMIT:
        return CommitDecision(
            should_commit=True,
            reason="Commit is guaranteed by configuration.",
            details={"hour_utc": current_hour_utc, "mode": "guaranteed"}
        )

    # --- Probabilistic Commit Path ---
    # Guaranteed commit on hours divisible by 3 (overrides standard probabilities).
    if current_hour_utc % 3 == 0:
        return CommitDecision(
            should_commit=True,
            reason=f"Guaranteed commit: Hour {current_hour_utc} UTC is a multiple of 3.",
            details={"hour_utc": current_hour_utc, "mode": "multiple_of_3"}
        )

    # Even hours logic
    if current_hour_utc % 2 == 0:
        threshold = Config.PROBABILITIES["even_hour"]
        roll = random.random()
        if roll < threshold:
            return CommitDecision(
                should_commit=True,
                reason=f"Success on even hour {current_hour_utc} UTC.",
                details={"hour_utc": current_hour_utc, "roll": f"{roll:.4f}", "threshold": threshold, "outcome": "success"}
            )
        else:
            return CommitDecision(
                should_commit=False,
                reason=f"Roll failed on even hour {current_hour_utc} UTC.",
                details={"hour_utc": current_hour_utc, "roll": f"{roll:.4f}", "threshold": threshold, "outcome": "failure"}
            )
    # Odd hours logic
    else:
        threshold = Config.PROBABILITIES["odd_hour"]
        roll = random.random()
        if roll < threshold:
            return CommitDecision(
                should_commit=True,
                reason=f"Success on odd hour {current_hour_utc} UTC.",
                details={"hour_utc": current_hour_utc, "roll": f"{roll:.4f}", "threshold": threshold, "outcome": "success"}
            )
        else:
            return CommitDecision(
                should_commit=False,
                reason=f"Roll failed on odd hour {current_hour_utc} UTC.",
                details={"hour_utc": current_hour_utc, "roll": f"{roll:.4f}", "threshold": threshold, "outcome": "failure"}
            )


def generate_commit_message(decision: CommitDecision) -> str:
    """Constructs a detailed, multi-line commit message."""
    header = Config.COMMIT_HEADER
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    body = Config.COMMIT_BODY_TEMPLATE.format(timestamp=timestamp)
    reason = Config.COMMIT_REASON_TEMPLATE.format(reason=decision.reason)

    # Adding the detailed context to the commit message for excellent traceability.
    details_str = "\n".join([f"- {key}: {value}" for key, value in decision.details.items()])

    # Combine all parts into a conventional commit format.
    return f"{header} {body}\n\n{reason}\n\n### Details\n{details_str}"


# ==================================================================================================
# --- FILE I/O OPERATIONS ---
# Separating file operations makes the code easier to reason about and test.
# ==================================================================================================
def write_log_entry(decision: CommitDecision, filepath: str) -> bool:
    """Appends the decision result to the target log file."""
    try:
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        content = f"{timestamp} - Commit Recommended. Reason: {decision.reason} | Details: {decision.details}\n"
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"Successfully wrote log entry to {filepath}")
        return True
    except (IOError, PermissionError) as e:
        logging.critical(f"Fatal I/O Error writing to log file {filepath}: {e}", exc_info=True)
        return False


def write_commit_message_file(message: str, filepath: str) -> bool:
    """
    Writes the generated commit message to a file.
    The GitHub Actions workflow will read this file to perform the commit.
    This decouples the message generation from the git execution.
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(message)
        logging.info(f"Successfully wrote commit message to {filepath}")
        return True
    except (IOError, PermissionError) as e:
        logging.critical(f"Fatal I/O Error writing to commit message file {filepath}: {e}", exc_info=True)
        return False


# ==================================================================================================
# --- MAIN ORCHESTRATOR ---
# ==================================================================================================
def main():
    """
    Main execution function to orchestrate the commit decision and file writing.
    Exit codes are used to signal the outcome to the CI/CD environment.
    - 0: Commit should proceed.
    - 1: A critical error occurred.
    - 2: No commit was decided (a clean, expected outcome).
    """
    # Determine script's directory to build absolute paths.
    # This is robust for different execution environments.
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    log_filepath = os.path.join(script_dir, Config.LOG_FILENAME)
    commit_msg_filepath = os.path.join(script_dir, Config.COMMIT_MSG_FILENAME)

    logging.basicConfig(level=Config.LOG_LEVEL, format=Config.LOG_FORMAT, stream=sys.stdout)
    logging.info("--- Dice Roll Committer Script Started ---")
    logging.info(f"Commit guaranteed mode: {Config.GUARANTEE_COMMIT}")

    # 1. Get the commit decision from the core logic.
    decision = get_commit_decision()
    logging.info(f"Decision made: should_commit={decision.should_commit}, Reason: {decision.reason}")

    if decision.should_commit:
        # 2. Generate the detailed commit message.
        commit_message = generate_commit_message(decision)

        # 3. Perform file I/O operations.
        log_written = write_log_entry(decision, log_filepath)
        msg_file_written = write_commit_message_file(commit_message, commit_msg_filepath)

        if log_written and msg_file_written:
            logging.info("Successfully updated log and created commit message file.")
            logging.info("--- Script Finished: Commit Recommended ---")
            sys.exit(0)
        else:
            logging.critical("Failed during file I/O operations. Aborting commit.")
            logging.info("--- Script Finished With CRITICAL Errors ---")
            sys.exit(1)
    else:
        # This block now provides the detailed "non-commit" reason.
        logging.info(f"No commit action will be taken. Reason: {decision.reason}")
        logging.info(f"Details: {decision.details}")
        logging.info("--- Script Finished: No Commit Recommended ---")
        sys.exit(2)


if __name__ == "__main__":
    main()