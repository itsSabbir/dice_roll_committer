# ==================================================================================================
# === ROBUST AUTOMATED GIT COMMITTER SCRIPT ========================================================
# ==================================================================================================
# This script intelligently decides whether to make a Git commit based on a multi-layered
# probabilistic model. The goal is to create a natural, organic-looking commit history.
#
# --- FEATURES ---
# 1. Quarter-Hourly Probabilities: Commit chances vary within each hour.
# 2. Weekday/Weekend Modifier: Commit chances are different for weekdays vs. weekends.
# 3. Seasonal Modifier: Commit chances vary based on the month of the year.
# 4. Decoupled Logic: All decisions are made here; the CI/CD workflow is just an executor.
# 5. Robust Configuration: All tunable parameters are in a central 'Config' class.
# 6. Detailed Logging: Provides excellent traceability for headless CI/CD runs.
# ==================================================================================================

import datetime
import random
import os
import sys
import logging
from dataclasses import dataclass
from typing import Dict, Any, Tuple

# ==================================================================================================
# --- CONFIGURATION CLASS: Centralizes all tunable parameters ---
# ==================================================================================================
class Config:
    """Holds all configuration variables for the script."""
    # --- File Configuration ---
    LOG_FILENAME: str = "dice_roll_log.txt"
    COMMIT_MSG_FILENAME: str = "commit_message.txt"

    # --- Global Behavior Configuration ---
    # Set to True to guarantee a commit every run, overriding all randomization.
    GUARANTEE_COMMIT: bool = False

    # --- LAYER 1: Base Probability Matrix (Quarter-Hourly) ---
    BASE_PROBABILITY: float = 0.25  # e.g., 25% chance for most quarters
    HALF_HOUR_DIP_PROBABILITY: float = 0.02 # e.g., 2% chance for the 30-44 min window

    # This tuple defines the probability pattern within a standard hour.
    # Format: (Q1: 00-14m, Q2: 15-29m, Q3: 30-44m, Q4: 45-59m)
    STANDARD_HOUR_PROBS: Tuple[float, float, float, float] = (
        BASE_PROBABILITY,
        BASE_PROBABILITY,
        HALF_HOUR_DIP_PROBABILITY,
        BASE_PROBABILITY
    )

    # Now, use the pre-defined variable to build the matrix.
    # The full 24-hour matrix is generated from the standard pattern.
    PROBABILITY_MATRIX: Dict[int, Tuple[float, float, float, float]] = {
        hour: STANDARD_HOUR_PROBS for hour in range(24)
    }

    # --- LAYER 2: Weekday/Weekend Modifier ---
    # Multiplies the base probability. > 1.0 increases chance, < 1.0 decreases it.
    WEEKDAY_MODIFIER: float = 1.0   # No change for weekdays
    WEEKEND_MODIFIER: float = 0.5   # 50% reduction on weekends

    # --- LAYER 3: Seasonal (Monthly) Modifier ---
    # A dictionary mapping the month number (1-12) to a probability modifier.
    SEASONAL_MODIFIERS: Dict[int, float] = {
        1: 1.1,  # Jan: New Year activity
        2: 1.0,  # Feb: Standard
        3: 1.0,  # Mar: Standard
        4: 1.1,  # Apr: Q2 push
        5: 0.9,  # May: Winding down for summer
        6: 0.8,  # Jun: Summer slowdown
        7: 0.7,  # Jul: Summer slowdown
        8: 0.8,  # Aug: Ramping back up
        9: 1.1,  # Sep: Q3 push
        10: 1.2, # Oct: High activity
        11: 1.25,# Nov: Peak end-of-year activity
        12: 1.0  # Dec: Holiday slowdown
    }

    # --- Git Commit Message Configuration ---
    COMMIT_HEADER: str = "chore(automated):"
    COMMIT_BODY_TEMPLATE: str = "Dice roll log update triggered at {timestamp} UTC."
    COMMIT_REASON_TEMPLATE: str = "Trigger Reason: {reason}"

    # --- Logging Configuration ---
    LOG_LEVEL = logging.INFO
    LOG_FORMAT: str = '%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'


# ==================================================================================================
# --- DATA CLASSES: For structured data transfer between functions ---
# ==================================================================================================
@dataclass
class CommitDecision:
    """Encapsulates the outcome of the commit decision logic."""
    should_commit: bool
    reason: str
    details: Dict[str, Any]


# ==================================================================================================
# --- CORE LOGIC ---
# ==================================================================================================
def get_commit_decision() -> CommitDecision:
    """
    Determines if a commit should be made based on a multi-layered probability model.
    """
    # Get all necessary time components. Always work in UTC.
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    current_hour = now_utc.hour
    current_minute = now_utc.minute
    current_weekday = now_utc.weekday() # Monday is 0, Sunday is 6
    current_month = now_utc.month

    logging.info(f"Evaluating commit logic for {now_utc.isoformat()} UTC...")

    # --- Override Path 1: Guaranteed by Config ---
    if Config.GUARANTEE_COMMIT:
        return CommitDecision(
            should_commit=True, reason="Commit is guaranteed by global configuration.",
            details={"mode": "guaranteed", "timestamp": now_utc.isoformat()}
        )

    # --- Override Path 2: Guaranteed by a special rule (e.g., time-based) ---
    if current_hour % 3 == 0:
        return CommitDecision(
            should_commit=True, reason=f"Guaranteed commit: Hour {current_hour} is a multiple of 3.",
            details={"mode": "multiple_of_3", "hour_utc": current_hour}
        )

    # --- Probabilistic Path: Calculate final probability from layers ---

    # Layer 1: Get Base Probability from Quarter-Hour Matrix
    if 0 <= current_minute <= 14: quarter_index = 0
    elif 15 <= current_minute <= 29: quarter_index = 1
    elif 30 <= current_minute <= 44: quarter_index = 2
    else: quarter_index = 3 # 45-59

    base_probability = Config.PROBABILITY_MATRIX.get(current_hour, (0,0,0,0))[quarter_index]

    # Layer 2: Get Weekday Modifier
    # Saturday (5) or Sunday (6)
    is_weekend = current_weekday >= 5
    weekday_modifier = Config.WEEKEND_MODIFIER if is_weekend else Config.WEEKDAY_MODIFIER

    # Layer 3: Get Seasonal Modifier
    # Use .get() with a default of 1.0 to handle any missing months gracefully
    seasonal_modifier = Config.SEASONAL_MODIFIERS.get(current_month, 1.0)

    # Calculate the final probability by combining the layers
    calculated_threshold = base_probability * weekday_modifier * seasonal_modifier

    # Clamp the final probability between 0.0 and 1.0 for correctness.
    final_threshold = max(0.0, min(1.0, calculated_threshold))

    # Perform the dice roll
    roll = random.random()

    decision_details = {
        "timestamp_utc": now_utc.isoformat(),
        "is_weekend": is_weekend,
        "quarter_of_hour": quarter_index + 1,
        "base_probability": f"{base_probability:.4f}",
        "weekday_modifier": weekday_modifier,
        "seasonal_modifier": seasonal_modifier,
        "final_threshold": f"{final_threshold:.4f}",
        "roll": f"{roll:.4f}",
    }

    if roll < final_threshold:
        decision_details["outcome"] = "success"
        reason_str = f"Success on {'weekend' if is_weekend else 'weekday'}, Q{quarter_index+1}. (Final Threshold: {final_threshold:.2%})"
        return CommitDecision(should_commit=True, reason=reason_str, details=decision_details)
    else:
        decision_details["outcome"] = "failure"
        reason_str = f"Roll failed on {'weekend' if is_weekend else 'weekday'}, Q{quarter_index+1}. (Final Threshold: {final_threshold:.2%})"
        return CommitDecision(should_commit=False, reason=reason_str, details=decision_details)


def generate_commit_message(decision: CommitDecision) -> str:
    """Constructs a detailed, multi-line commit message."""
    header = Config.COMMIT_HEADER
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    body = Config.COMMIT_BODY_TEMPLATE.format(timestamp=timestamp)
    reason = Config.COMMIT_REASON_TEMPLATE.format(reason=decision.reason)
    details_str = "\n".join([f"- {key}: {value}" for key, value in decision.details.items()])

    return f"{header} {body}\n\n{reason}\n\n### Details\n{details_str}"


# ==================================================================================================
# --- FILE I/O OPERATIONS ---
# ==================================================================================================
def write_log_entry(decision: CommitDecision, filepath: str) -> bool:
    """Appends the decision result to the target log file."""
    try:
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        content = f"{timestamp} - Commit Recommended: {decision.should_commit} | Reason: {decision.reason} | Details: {decision.details}\n"
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"Successfully wrote log entry to {filepath}")
        return True
    except (IOError, PermissionError) as e:
        logging.critical(f"Fatal I/O Error writing to log file {filepath}: {e}", exc_info=True)
        return False

def write_commit_message_file(message: str, filepath: str) -> bool:
    """Writes the generated commit message to a file for the CI/CD workflow."""
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
    Main execution function. Exit codes signal the outcome to the CI/CD environment.
    - 0: Commit Recommended
    - 1: Critical Error
    - 2: No Commit Decided (Clean Exit)
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd() # Fallback for interactive environments

    log_filepath = os.path.join(script_dir, Config.LOG_FILENAME)
    commit_msg_filepath = os.path.join(script_dir, Config.COMMIT_MSG_FILENAME)

    logging.basicConfig(level=Config.LOG_LEVEL, format=Config.LOG_FORMAT, stream=sys.stdout)
    logging.info("--- Dice Roll Committer Script Started ---")

    decision = get_commit_decision()
    logging.info(f"Decision: should_commit={decision.should_commit}, Reason: {decision.reason}")

    # Always write a log entry, regardless of the decision, for full traceability.
    if not write_log_entry(decision, log_filepath):
        logging.critical("Failed to write to the main log file. Aborting.")
        logging.info("--- Script Finished With CRITICAL ERRORS (Exit 1) ---")
        sys.exit(1)

    if decision.should_commit:
        commit_message = generate_commit_message(decision)
        if write_commit_message_file(commit_message, commit_msg_filepath):
            logging.info("--- Script Finished: COMMIT RECOMMENDED (Exit 0) ---")
            sys.exit(0)
        else:
            logging.critical("Failed commit message file I/O. Aborting commit.")
            logging.info("--- Script Finished With CRITICAL ERRORS (Exit 1) ---")
            sys.exit(1)
    else:
        logging.info(f"Details: {decision.details}")
        logging.info("--- Script Finished: NO COMMIT RECOMMENDED (Exit 2) ---")
        sys.exit(2)


if __name__ == "__main__":
    main()