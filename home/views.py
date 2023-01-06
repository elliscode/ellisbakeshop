from django.core.exceptions import ValidationError
from django.core.mail import send_mail, BadHeaderError
from django.core.validators import validate_email
from django.http import HttpResponse
from django.shortcuts import render
import re

from ellisbakeshop.settings import EMAIL_HOST_USER


# Create your views here.
def index(request):
    return render(request, 'home/index.html', context={})


def placeorder(request):
    email_address = request.POST.get('email')
    try:
        validate_email(email_address)
    except ValidationError as e:
        return HttpResponse(status=500)

    only_numbers_and_letters_regex = '[^a-zA-Z0-9 ]'

    name = request.POST.get('name', 'Forgot to put')
    name = re.sub(only_numbers_and_letters_regex, '_', name, )

    only_numbers = '[^0-9]+';
    telephone = request.POST.get('tel', '(000) 000-0000')
    telephone = re.sub(only_numbers, '', telephone, )

    date = request.POST.get('date')

    order = request.POST.get('order')

    # if I'm reading this right, I don't have to worry about header injection in the message?
    # https://docs.djangoproject.com/en/4.1/topics/email/#preventing-header-injection
    email_content = 'Thank you for your order!' + '\n' \
                    + 'This is a copy for your records, we will reply with a confirmation shortly.' + '\n\n' \
                    + 'Name: {name}' + '\n' \
                    + 'Telephone Number: {tel}' + '\n' \
                    + 'Date: {date}' + '\n' \
                    + 'Order: \n{order}'

    try:
        send_mail(subject='Ellis Bake Shop Order Form: ' + name,
                  message=email_content.format(name=name, tel=telephone, date=date, order=order, ),
                  from_email=EMAIL_HOST_USER,
                  recipient_list=[EMAIL_HOST_USER], fail_silently=False, )
    except BadHeaderError:
        return HttpResponse(status=500)
    return HttpResponse(status=204)
