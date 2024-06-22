import http.server
import socketserver
import json
from urllib.parse import urlparse, parse_qs

PORT = 8000
ADMIN_TOKEN = 'admin123'

class Customer:
    def __init__(self, name, ticket_number):
        self.name = name
        self.ticket_number = ticket_number
        self.status = 'WAITING'

class QueueManagementSystem:
    def __init__(self):
        self.customers = []
        self.served_customers = []

    def add_customer(self, name, ticket_number):
        customer = Customer(name, ticket_number)
        self.customers.append(customer)
        print(f"Customer {name} with ticket number {ticket_number} added to the queue.")

    def serve_next_customer(self):
        if self.customers:
            # Sort customers based on ticket number in ascending order
            self.customers.sort(key=lambda x: int(x.ticket_number))
            customer = self.customers.pop(0)
            customer.status = 'SERVED'
            self.served_customers.append(customer)
            print(f"Customer {customer.name} with ticket number {customer.ticket_number} has been served.")
            return customer
        else:
            print("No customers in the queue.")
            return None

    def remove_next_customer(self):
        if self.customers:
            # Find the index of the customer with the lowest ticket number
            min_index = 0
            for i in range(1, len(self.customers)):
                if int(self.customers[i].ticket_number) < int(self.customers[min_index].ticket_number):
                    min_index = i
            removed_customer = self.customers.pop(min_index)
            print(f"Customer {removed_customer.name} with ticket number {removed_customer.ticket_number} has been removed.")
            return removed_customer
        else:
            print("No customers in the queue to remove.")
            return None


    def get_queue(self):
        return [{'name': customer.name, 'ticket_number': customer.ticket_number, 'status': customer.status} for customer in self.customers]

    def get_served_customers(self):
        return [{'name': customer.name, 'ticket_number': customer.ticket_number, 'status': customer.status} for customer in self.served_customers]

qms = QueueManagementSystem()

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url_parts = urlparse(self.path)
        query_params = parse_qs(url_parts.query)
        if url_parts.path == '/queue':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(qms.get_queue()).encode())
        else:
            super().do_GET()

    def do_DELETE(self):
        url_parts = urlparse(self.path)
        query_params = parse_qs(url_parts.query)
        if url_parts.path == '/remove/next':
            if 'admin_token' in query_params and query_params['admin_token'][0] == ADMIN_TOKEN:
                removed_customer = qms.remove_next_customer()
                if removed_customer:
                    response_data = {'removed_customer': removed_customer.name}
                else:
                    response_data = {'message': 'No customers in the queue to remove.'}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())
            else:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'Forbidden')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def do_POST(self):
        if self.path == '/add':
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            name = post_data['name']
            ticket_number = post_data['ticket_number']
            qms.add_customer(name, ticket_number)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

Handler = MyRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
