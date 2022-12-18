from waitress import serve

from ellisbakeshop.wsgi import application

if __name__ == '__main__':
    serve(application, port='8002')