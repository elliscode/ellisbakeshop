import os
import re
import json
import boto3
from botocore.exceptions import ClientError

ADMIN_PHONE = os.environ['ADMIN_PHONE']
ADMIN_SENDER_EMAIL = os.environ['ADMIN_SENDER_EMAIL']
ADMIN_RECIPIENT_EMAIL = os.environ['ADMIN_RECIPIENT_EMAIL']
SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']
sqs = boto3.client("sqs")

def lambda_handler(event, context):
    print(json.dumps(event))
    if event['httpMethod'] != 'POST' or not 'origin' in event['headers'] or not event['headers']['origin'].startswith('https://www.ellisbakeshop.com'):
        return {
            "statusCode": 403,
            "body": "Forbidden",
            "headers": {
                "Access-Control-Allow-Origin": "*",
            }
        }
        
    body = parse_body(event['body'])
    name = body['name']
    phone = body['tel']
    email = body['email']
    date = body['date']
    order = body['order']
    
    send_email(name, phone, email, date, order)
    send_text(name, phone, email, date, order)
    parsed_phone = parse_valid_us_phone_number(phone)
    if parsed_phone:
        send_ack(parsed_phone)
    
    return {
        "statusCode": 200,
        "body": "Successfully submitted order",
        "headers": {
            "Access-Control-Allow-Origin": "https://www.ellisbakeshop.com",
        }
    }
    
def parse_body(body):
    if isinstance(body, dict):
        return body
    elif body.startswith("{"):
        return json.loads(body)
    else:
        return dict(parse_qsl(body))
        

def send_ack(phone):
    # generate and send message if you are creating a new otp
    message = {
        "phone": phone,
        "message": f"Thank you for placing your order at ellisbakeshop.com! I will reach out shortly to confirm the details of your order.",
    }
    print(message)
    sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(message)
    )


def parse_valid_us_phone_number(phone):
    stripped_number = re.sub('[^\d]+', '', phone)
    if stripped_number.startswith('1'):
        stripped_number = stripped_number[1:]
    if len(stripped_number) == 10:
        return stripped_number
    return None
        

def send_text(name, phone, email, date, order):
    # generate and send message if you are creating a new otp
    message = {
        "phone": ADMIN_PHONE,
        "message": f"You received an order on ellisbakeshop from:\n{name}\n{phone}\n{email}\n{date}",
    }
    print(message)
    sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(message)
    )


def send_email(name, phone, email, date, order):
    SENDER = ADMIN_SENDER_EMAIL # must be verified in AWS SES Email
    RECIPIENT = ADMIN_RECIPIENT_EMAIL # must be verified in AWS SES Email

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-1"

    # The subject line for the email.
    SUBJECT = f"Thanks {name} for your order!"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = f"""Thanks for your order!
Thanks for placing your order with ellisbakeshop.com, here is a summary:
- {name}
- {phone}
- {email}
- {date}
- {order}
"""
                
    # The HTML body of the email.
    BODY_HTML = f"""<html>
    <head></head>
    <body>
    <h1>Thanks for your order!</h1>
    <p>Thanks for placing your order with ellisbakeshop.com, here is a summary:</p>
    <ul>
        <li>{name}</li>
        <li>{phone}</li>
        <li>{email}</li>
        <li>{date}</li>
    </ul>
    <pre>{order}</pre>
    </body>
    </html>
    """

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Data': BODY_HTML
                    },
                    'Text': {
                        'Data': BODY_TEXT
                    },
                },
                'Subject': {
                    'Data': SUBJECT
                },
            },
            Source=SENDER
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
