# dice_roll_committer.py
import datetime
import random
import os
import sys
import logging

# --- Configuration ---
TARGET_FILENAME: str = "dice_roll_log.txt"
LOG_FORMAT: str = '%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, stream=sys.stdout)

# Determine the absolute path for the target file relative to the script's location
try:
    SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR: str = os.getcwd()
TARGET_FILEPATH: str = os.path.join(SCRIPT_DIR, TARGET_FILENAME)

# --- Helper Functions ---
def should_commit() -> tuple[bool, str]:
    """
    Determines if a commit should be made based on the current hour and dice rolls.
    Returns a tuple: (True/False for commit, reason_string)
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    current_hour_utc = now_utc.hour  # 0-23

    logging.info(f"Current UTC hour: {current_hour_utc}")

    # Special hours (3, 6, 9, 12, 15, 18, 21, 0 - for 00 hour)
    # Note: Python's % (modulo) works as expected for these.
    if current_hour_utc % 3 == 0:
        reason = f"Guaranteed commit: Current hour {current_hour_utc} UTC is a multiple of 3."
        logging.info(reason)
        return True, reason

    # Even hours (excluding those covered by multiples of 3)
    if current_hour_utc % 2 == 0:
        roll = random.random()  # float between 0.0 and 1.0
        if roll < 0.50: # 50% chance
            reason = f"Commit chance on even hour {current_hour_utc} UTC: Rolled {roll:.2f} (success < 0.50)."
            logging.info(reason)
            return True, reason
        else:
            reason = f"No commit on even hour {current_hour_utc} UTC: Rolled {roll:.2f} (fail >= 0.50)."
            logging.info(reason)
            return False, reason
    # Odd hours (excluding those covered by multiples of 3)
    else:
        roll = random.random() # float between 0.0 and 1.0
        if roll < 0.25: # 25% chance
            reason = f"Commit chance on odd hour {current_hour_utc} UTC: Rolled {roll:.2f} (success < 0.25)."
            logging.info(reason)
            return True, reason
        else:
            reason = f"No commit on odd hour {current_hour_utc} UTC: Rolled {roll:.2f} (fail >= 0.25)."
            logging.info(reason)
            return False, reason

def write_to_file(reason: str) -> bool:
    """
    Appends a timestamp and the reason to the target file.
    """
    try:
        timestamp_utc = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        content_to_write = f"{timestamp_utc} - Commit triggered. Reason: {reason}\n"

        # Ensure the directory for the file exists (though usually it's the repo root)
        os.makedirs(os.path.dirname(TARGET_FILEPATH), exist_ok=True)

        with open(TARGET_FILEPATH, "a", encoding="utf-8") as f:
            f.write(content_to_write)
        logging.info(f"Successfully wrote to {TARGET_FILEPATH}")
        return True
    except IOError as e:
        logging.error(f"IOError writing to file {TARGET_FILEPATH}: {e}", exc_info=True)
        return False
    except Exception as e:
        logging.error(f"Unexpected error writing to file {TARGET_FILEPATH}: {e}", exc_info=True)
        return False

def main():
    """
    Main execution function.
    Determines if a commit should happen, writes to a file, and exits with appropriate status.
    Exit codes:
    0: Commit should proceed (file was modified).
    2: No commit decided (file was NOT modified).
    1: Error occurred.
    """
    logging.info("--- Dice Roll Committer Script Started ---")

    perform_commit, reason_for_decision = should_commit()

    if perform_commit:
        if write_to_file(reason_for_decision):
            logging.info("Decision: COMMIT. File updated.")
            logging.info("--- Dice Roll Committer Script Finished: Commit Recommended ---")
            sys.exit(0) # Indicate that changes were made and commit should happen
        else:
            logging.error("Error writing to file, aborting commit recommendation.")
            logging.info("--- Dice Roll Committer Script Finished With Errors ---")
            sys.exit(1) # Indicate error
    else:
        logging.info("Decision: DO NOT COMMIT. File not modified.")
        logging.info("--- Dice Roll Committer Script Finished: No Commit Recommended ---")
        # Use a distinct exit code to signal "no action needed" to the workflow
        sys.exit(2) # Indicate no changes were made, skip commit


if __name__ == "__main__":
    main()