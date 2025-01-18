import grpc
from concurrent import futures
import calculator_pb2
import calculator_pb2_grpc
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class CalculatorServicer(calculator_pb2_grpc.CalculatorServicer):
    def Add(self, request, context):
        # Log the request details
        logging.info(f"Received Add request: num1={request.num1}, num2={request.num2}")
        
        # Perform the addition
        result = request.num1 + request.num2
        
        # Log the result
        logging.info(f"Sending Add response: result={result}")
        return calculator_pb2.AddResponse(result=result)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    calculator_pb2_grpc.add_CalculatorServicer_to_server(CalculatorServicer(), server)
    server.add_insecure_port('[::]:50051')
    
    # Log server start
    logging.info("Starting gRPC server on port 50051")
    
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
