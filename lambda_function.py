import json
import sendInstance

def lambda_handler(event, context):
    # TODO implement
    sendInstance.main()
    print("Everything OK")
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

if __name__ == "__main__":   
    lambda_handler('', '')
