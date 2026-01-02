import azure.functions as func
import json
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('HTTP trigger function processed a request.')

   
    
  if name:
        response_data = {
            "message": f"Hello, {name}! Welcome to Azure Serverless Functions! 🚀",
            "status": "success",
            "timestamp": "2026-01-02"
        }
        return func.HttpResponse(
            json.dumps(response_data),
            mimetype="application/json",
            status_code=200
        )
    else:
        return func.HttpResponse(
            json.dumps({"error": "Please pass a name in the query string or request body"}),
            mimetype="application/json",
            status_code=400
        )
