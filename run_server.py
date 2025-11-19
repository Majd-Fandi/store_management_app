from waitress import serve
from store_management.wsgi import application

if __name__ == '__main__':
    print("Serving on http://127.0.0.1:8080")
    
    # Add 'threads=10' (Default is usually 4)
    # This allows 10 simultaneous files to be served at once.
    serve(application, host='127.0.0.1', port=8080, threads=10)

# if __name__ == '__main__':
#     print("Serving on http://127.0.0.1:8080")
#     serve(application, host='127.0.0.1', port=8080)