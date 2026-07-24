import schedule
import time
import logging
from datetime import datetime
from typing import Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScheduler:
    def __init__(self):
        """Initialize the scheduler."""
        self.jobs = []
    
    def schedule_job(self, job_func: Callable, interval_minutes: int, 
                    run_on_startup: bool = True):
        """
        Schedule a job to run at specified intervals.
        
        Args:
            job_func (Callable): Function to run
            interval_minutes (int): Interval in minutes
            run_on_startup (bool): Whether to run immediately on startup
        """
        # Run job immediately if requested
        if run_on_startup:
            logger.info("Running job on startup")
            try:
                job_func()
            except Exception as e:
                logger.error(f"Error running job on startup: {str(e)}")
        
        # Schedule job to run at intervals
        job = schedule.every(interval_minutes).minutes.do(job_func)
        self.jobs.append(job)
        
        logger.info(f"Scheduled job to run every {interval_minutes} minutes")
    
    def run_scheduler(self):
        """Run the scheduler indefinitely."""
        logger.info("Starting scheduler...")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler: {str(e)}")
                time.sleep(10)  # Wait before retrying
    
    def clear_jobs(self):
        """Clear all scheduled jobs."""
        for job in self.jobs:
            schedule.cancel_job(job)
        self.jobs = []
        logger.info("Cleared all scheduled jobs")

def get_next_run_time() -> str:
    """
    Get the next scheduled run time.
    
    Returns:
        str: Human-readable next run time
    """
    try:
        next_run = schedule.next_run()
        if next_run:
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return "No jobs scheduled"
    except Exception as e:
        logger.error(f"Error getting next run time: {str(e)}")
        return "Unknown"