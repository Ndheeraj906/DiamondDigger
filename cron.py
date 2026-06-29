from app import trigger_weekly

if __name__ == "__main__":
    print("Running scheduled weekly email job...")
    trigger_weekly()
    print("Job complete.")
