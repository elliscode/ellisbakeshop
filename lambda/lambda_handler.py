import json
import traceback
from botocore.exceptions import ClientError
from ellisbakeshop.utils import (
    otp_route,
    login_route,
    path_equals,
    format_response,
    ios_cookie_refresh_route,
    path_starts_with,
    clear_all_tokens_route,
    authenticate,
    TWILIO_NUMBER_TO_SEND_THE_MESSAGE_FROM,
    urllib,
    re,
    ADMIN_PHONE,
    sqs,
    SMS_SQS_QUEUE_URL,
    dynamo,
    TABLE_NAME,
    python_obj_to_dynamo_obj,
    dynamo_obj_to_python_obj,
    time,
    os,
    boto3,
)

ADMIN_SENDER_EMAIL = os.environ['ADMIN_SENDER_EMAIL']
ADMIN_RECIPIENT_EMAIL = os.environ['ADMIN_RECIPIENT_EMAIL']

def lambda_handler(event, context):
    try:
        print(json.dumps(event))
        result = route(event)
        print(result)
        return result
    except Exception:
        traceback.print_exc()
        return format_response(event=event, http_code=500, body="Internal server error")
        
        
def health_route(event):
    return format_response(event=event, http_code=200, body="Healthy")
    
    
@authenticate
def login_test_route(event, user_data, body):
    return format_response(event=event, http_code=200, body="You are logged in")
    
    
def receive_route(event):
    print(event)

    parsed_body = urllib.parse.parse_qs(event["body"])

    print(parsed_body)

    from_number = parse_valid_us_phone_number(parsed_body["From"][0])

    if not from_number:
        message = {
            "phone": ADMIN_PHONE,
            "message": f"Received a text message from {from_number} which is not valid",
        }
        print(message)
        return {
            "statusCode": 200,
            "body": "<Response/>",
            "headers": {
                "Content-Type": "application/xml",
            },
        }

    print(f"Received a text message from {from_number}, checking if account exists...")

    username = parse_valid_us_phone_number(from_number)
    
    print(username)

    msg_text = parsed_body["Body"][0]

    print(msg_text)

    store_communication(from_number, from_number, msg_text)

    if parse_valid_us_phone_number(ADMIN_PHONE) != parse_valid_us_phone_number(TWILIO_NUMBER_TO_SEND_THE_MESSAGE_FROM):
        message = {
            "phone": ADMIN_PHONE, 
            "message": f"ellisbakeshop.com\nFrom: {username}\nMessage: {msg_text[:116]}",
            "sender": TWILIO_NUMBER_TO_SEND_THE_MESSAGE_FROM,
        }
        print(message)
        sqs.send_message(
            QueueUrl=SMS_SQS_QUEUE_URL,
            MessageBody=json.dumps(message),
        )

    return {
        "statusCode": 200,
        "body": "<Response/>",
        "headers": {
            "Content-Type": "application/xml",
        },
    }
    

def store_communication(parsed_customer_phone, parsed_sender_phone, msg_text, metadata={}):
    response = dynamo.get_item(
        TableName=TABLE_NAME,
        Key=python_obj_to_dynamo_obj({"key1": f"customer", "key2": parsed_customer_phone}),
    )
    
    items = []
    msg_time = int(time.mktime(time.gmtime()))
    if "Item" in response:
        user_data = dynamo_obj_to_python_obj(response["Item"])
    else:
        user_data = {"key1": f"customer", "key2": f"{parsed_customer_phone}"}
    
    user_data["last_message_time"] = msg_time
    if 'email' in metadata and metadata['email']:
        user_data["email"] = metadata['email']
    if 'name' in metadata and metadata['name']:
        user_data["name"] = metadata['name']
        
    items.append({"PutRequest": {"Item": python_obj_to_dynamo_obj(user_data)}})
    items.append({"PutRequest": {"Item": python_obj_to_dynamo_obj({"key1": f"message_{parsed_customer_phone}", "key2": f"{msg_time}", "message": msg_text, 'from': parsed_sender_phone})}})
    response = dynamo.batch_write_item(RequestItems={TABLE_NAME: items})
    
    
@authenticate
def get_customers_route(event, user_data, body):
    response = dynamo.query(
        TableName=TABLE_NAME,
        KeyConditions={
            "key1": {
                "AttributeValueList": [{"S": f"customer"}],
                "ComparisonOperator": "EQ",
            },
        },
    )
    phone_list = []
    for item in response.get("Items", []):
        python_item = dynamo_obj_to_python_obj(item)
        customer_data = {'phone': python_item["key2"]}
        if python_item.get('email'):
            customer_data['email'] = python_item.get('email')
        if python_item.get('name'):
            customer_data['name'] = python_item.get('name')
        phone_list.append(customer_data)
    return format_response(event=event, http_code=200, body=phone_list)
    
    
@authenticate
def get_messages_route(event, user_data, body):
    if 'phone' not in body:
        return format_response(event=event, http_code=400, body="You need to supply a phone number")
    phone = parse_valid_us_phone_number(body['phone'])
    if not phone:
        return format_response(event=event, http_code=400, body="You need to supply a valid US phone number")
    output = []
    response = dynamo.query(
        TableName=TABLE_NAME,
        KeyConditions={
            "key1": {
                "AttributeValueList": [{"S": f"message_{phone}"}],
                "ComparisonOperator": "EQ",
            },
        },
        ScanIndexForward=False,
    )
    for item in response.get("Items", []):
        print(item)
        python_item = dynamo_obj_to_python_obj(item)
        output.append(python_item)
    return format_response(event=event, http_code=200, body=output)
    
    
@authenticate
def send_message_route(event, user_data, body):
    if 'phone' not in body:
        return format_response(event=event, http_code=400, body="You need to supply a phone number")
    phone = parse_valid_us_phone_number(body['phone'])
    if not phone:
        return format_response(event=event, http_code=400, body="You need to supply a valid US phone number")
    if 'message' not in body or not body['message']:
        return format_response(event=event, http_code=400, body="You need to supply a message to send")
        
    username = phone
    msg_text = body['message']
    
    store_communication(username, parse_valid_us_phone_number(TWILIO_NUMBER_TO_SEND_THE_MESSAGE_FROM), msg_text)

    if parse_valid_us_phone_number(username) != parse_valid_us_phone_number(TWILIO_NUMBER_TO_SEND_THE_MESSAGE_FROM):
        message = {
            "phone": username, 
            "message": f"{msg_text}",
            "sender": TWILIO_NUMBER_TO_SEND_THE_MESSAGE_FROM,
        }
        print(message)
        sqs.send_message(
            QueueUrl=SMS_SQS_QUEUE_URL,
            MessageBody=json.dumps(message),
        )
    
    return format_response(event=event, http_code=200, body="Sent the message to the user")
    

def parse_valid_us_phone_number(phone):
    stripped_number = re.sub('[^\d]+', '', phone)
    if stripped_number.startswith('1'):
        stripped_number = stripped_number[1:]
    if len(stripped_number) == 10:
        return stripped_number
    return None
    

def order_route(event):
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
    
    email_text = send_email(name, phone, email, date, order)
    send_text(name, phone, email, date, order)
    parsed_phone = parse_valid_us_phone_number(phone)
    if parsed_phone:
        send_confirmation_text(parsed_phone)
        store_communication(parsed_phone, parsed_phone, email_text, {'name': name, 'email': email})
    
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
        

def send_text(name, phone, email, date, order):
    if parse_valid_us_phone_number(ADMIN_PHONE) != parse_valid_us_phone_number(TWILIO_NUMBER_TO_SEND_THE_MESSAGE_FROM):
        message = {
            "phone": ADMIN_PHONE,
            "message": f"You received an order on ellisbakeshop from:\n{name}\n{phone}\n{email}\n{date}",
            "sender": TWILIO_NUMBER_TO_SEND_THE_MESSAGE_FROM,
        }
        print(message)
        sqs.send_message(
            QueueUrl=SMS_SQS_QUEUE_URL,
            MessageBody=json.dumps(message)
        )
    
    
def send_confirmation_text(phone):
    if parse_valid_us_phone_number(phone) != parse_valid_us_phone_number(TWILIO_NUMBER_TO_SEND_THE_MESSAGE_FROM):
        message = {
            "phone": f"+1{phone}",
            "message": f"Thank you for placing your order on ellisbakeshop! I will reach out to confirm the details of your order shortly.",
            "sender": TWILIO_NUMBER_TO_SEND_THE_MESSAGE_FROM,
        }
        print(message)
        sqs.send_message(
            QueueUrl=SMS_SQS_QUEUE_URL,
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
        
    return BODY_TEXT



# Only using POST because I want to prevent CORS preflight checks, and setting a
# custom header counts as "not a simple request" or whatever, so I need to pass
# in the CSRF token (don't want to pass as a query parameter), so that really
# only leaves POST as an option, as GET has its body removed by AWS somehow
#
# see https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS#simple_requests
def route(event):
    if path_equals(event=event, method="POST", path="/health"):
        return health_route(event)
    if path_equals(event=event, method="POST", path="/otp"):
        return otp_route(event)
    if path_equals(event=event, method="POST", path="/login"):
        return login_route(event)
    if path_equals(event=event, method="POST", path="/logout-all"):
        return clear_all_tokens_route(event)
    if path_equals(event=event, method="POST", path="/login-test"):
        return login_test_route(event)
    if path_equals(event=event, method="POST", path="/receive"):
        return receive_route(event)
    if path_equals(event=event, method="POST", path="/messages/receive"):
        return receive_route(event)
    if path_equals(event=event, method="POST", path="/messages/get"):
        return get_messages_route(event)
    if path_equals(event=event, method="POST", path="/customers/get"):
        return get_customers_route(event)
    if path_equals(event=event, method="POST", path="/messages/send"):
        return send_message_route(event)
    if path_equals(event=event, method="POST", path="/order"):
        return order_route(event)
    if path_equals(event=event, method="POST", path="/submitorder"):
        return order_route(event)

    return format_response(event=event, http_code=404, body="No matching route found")
