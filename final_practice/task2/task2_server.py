import grpc
from concurrent.futures import ThreadPoolExecutor
import calculator_pb2 as stub
import calculator_pb2_grpc as service

SERVER_ADDR = '0.0.0.0:50000'

class Calculator(service.CalculatorServicer):
    def __init__(self):
        try:
            self.executor = ThreadPoolExecutor(max_workers=10)
        except Exception as error:
            print("Error in Calculator.__init__(): ", error)
        
    def Add(self, request, context):
        a = request.a
        b = request.b
        print("Add({}, {})".format(a, b))
        res = float(a) + float(b)
        return stub.ResponseMessage(result=res, zero=False, message="")
    def Subtract(self, request, context):
        a = request.a
        b = request.b
        print("Subtract({}, {})".format(a, b))
        res = float(a) - float(b)
        return stub.ResponseMessage(result=res, zero=False, message="")
    def Multiply(self, request, context):
        a = request.a
        b = request.b
        print("Multiply({}, {})".format(a, b))
        res = float(a) * float(b)
        return stub.ResponseMessage(result=res, zero=False, message="")
    def Divide(self, request, context):
        a = request.a
        b = request.b
        print("Divide({}, {})".format(a, b))
        if b == 0:
            return stub.ResponseMessage(result=0, zero=True, message="nan")
        else:
            res = float(a) / float(b)
            return stub.ResponseMessage(result=res, zero=False, message="")
        
if __name__ == '__main__':
    server = grpc.server(Calculator().executor)
    try:
        service.add_CalculatorServicer_to_server(Calculator(), server)
        server.add_insecure_port(SERVER_ADDR)
        server.start()
        print("Server listening on " + SERVER_ADDR)
        server.wait_for_termination()
    except KeyboardInterrupt as error:
        print("\nShutting down server...")
        server.stop(0)