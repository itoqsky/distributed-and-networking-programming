import grpc

import calculator_pb2 as service
import calculator_pb2_grpc as stub

def add(a, b):
    args = service.Input(a=a, b=b)
    response = stub.Add(args)
    print(f"Add({a}, {b}) = {response.result}")

def subtract(a, b):
    args = service.Input(a=a, b=b)
    response = stub.Subtract(args)
    print(f"Subtract({a}, {b}) = {response.result}")

def multiply(a, b):
    args = service.Input(a=a, b=b)
    response = stub.Multiply(args)
    print (f"Multiply({a}, {b}) = {response.result}")

def divide(a, b):
    args = service.Input(a=a, b=b)
    response = stub.Divide(args)
    if response.zero == True:
        print(f"Divide({a}, {b}) = {response.message}")
    else:
        print(f"Divide({a}, {b}) = {response.result}")

if __name__ == '__main__':
    with grpc.insecure_channel('0.0.0.0:50000') as channel:
        stub = stub.CalculatorStub(channel)
        add(10, 2)
        subtract(10, 2)
        multiply(10, 2)
        divide(10, 2)
        divide(10,0)
