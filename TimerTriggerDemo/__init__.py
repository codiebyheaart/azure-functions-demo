import azure.functions as func
import logging
import datetime

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

   if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info(f'Timer trigger function ran at {utc_timestamp}')
    logging.info('This function runs every 5 minutes! ⏰')
