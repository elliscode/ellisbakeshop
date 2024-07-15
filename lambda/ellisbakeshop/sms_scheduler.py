import json
import re
from .utils import (
    ADMIN_PHONE,
    DOMAIN_NAME,
    get_user_data,
    format_response,
    sqs,
    authenticate,
    python_obj_to_dynamo_obj,
    dynamo,
    TABLE_NAME,
    dynamo_obj_to_python_obj,
    create_id,
    SMS_SQS_QUEUE_URL,
    SMS_SQS_QUEUE_ARN,
    SMS_SCHEDULER_ROLE_ARN,
    scheduler,
)


def schedule_sms(event, time_to_send, message_text):
    if not time_to_send or not re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}").match(time_to_send):
        return format_response(
            event=event,
            http_code=400,
            body="You must supply a time in the format yyyy-mm-ddThh:mm:ss",
        )
    if not message_text:
        return format_response(
            event=event,
            http_code=400,
            body="You must supply a message",
        )
    message_dict = {
        "phone": ADMIN_PHONE,
        "message": message_text,
    }
    message_to_send = json.dumps(message_dict)
    schedule_name = f"ellisbakeshop_schedule_{re.sub(r'[^a-z0-9]','_', time_to_send)}"
    group_name = f"ellisbakeshop_schedule_group"
    response = {}
    try:
        response = scheduler.get_schedule_group(Name=group_name)
    except Exception as e:
        response = scheduler.create_schedule_group(Name=group_name)
    try:
        response = scheduler.create_schedule(
            ActionAfterCompletion="DELETE",
            FlexibleTimeWindow={
                "Mode": "OFF",
            },
            GroupName=group_name,
            Name=schedule_name,
            ScheduleExpression=f"at({time_to_send})",
            ScheduleExpressionTimezone="America/New_York",
            State="ENABLED",
            Target={
                "Arn": SMS_SQS_QUEUE_ARN,
                "Input": message_to_send,
                "RetryPolicy": {
                    "MaximumRetryAttempts": 0,
                },
                "RoleArn": SMS_SCHEDULER_ROLE_ARN,
            },
        )
    except:
        print("Error creating schedule due to conflict")

    return format_response(
        event=event,
        http_code=200,
        body=f"Scheduled a message for {time_to_send}",
    )
