import datetime

print(datetime.datetime.now())
print(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
print(datetime.datetime.now().astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"))
parsed_date = datetime.datetime.strptime("2024-06-30T10:00:00", "%Y-%m-%dT%H:%M:%S").astimezone(datetime.timezone.utc)
print(parsed_date)
reminder_date = parsed_date - datetime.timedelta(hours=14)
while reminder_date > datetime.datetime.now().astimezone(datetime.timezone.utc):
    print(reminder_date)
    reminder_date = reminder_date - datetime.timedelta(days=1)
print("end")
