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
    name = request.POST.get('name')
    name = re.sub(only_numbers_and_letters_regex, '_', name, )

    # if I'm reading this right, I don't have to worry about header injection in the message?
    # https://docs.djangoproject.com/en/4.1/topics/email/#preventing-header-injection
    message = request.POST.get('order')
    message = "This is a copy of the order you placed on Ellis Bake Shop for your records," \
              + " we will reply separately with a confirmation.\n\n" + message

    try:
        send_mail(subject='Ellis Bake Shop Order Form: ' + name,
                  message=message,
                  from_email=EMAIL_HOST_USER,
                  recipient_list=[email_address, EMAIL_HOST_USER], fail_silently=False, )
    except BadHeaderError:
        return HttpResponse(status=500)
    return HttpResponse(status=204)
