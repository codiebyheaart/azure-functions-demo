import azure.functions as func
import logging

def main(myblob: func.InputStream):
    logging.info(f"Blob trigger function processed blob \n"
                 f"Name: {myblob.name}\n"
                 f"Blob Size: {myblob.length} bytes")

# You can process the blob content here
    content = myblob.read()
    logging.info(f"Blob content (first 100 chars): {content[:100]}")
