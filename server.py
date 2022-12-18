from waitress import serve

from elliscodedotcom.wsgi import application

if __name__ == '__main__':
    serve(application, port='8001')