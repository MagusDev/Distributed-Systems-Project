from prometheus_client import start_http_server, Counter, Gauge, Histogram, Summary
import threading
import psutil
import time

class ServiceMonitor:
    def __init__(self, service_name, metrics_port):
        # Response times and latencies
        self.request_latency = Histogram(
            f'{service_name}_request_latency_seconds',
            'Request latency in seconds',
            ['operation'],  # Add label for operation type
            buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0)
        )
        
        # Message throughput with labels
        self.messages_total = Counter(
            f'{service_name}_messages_total',
            'Total number of messages processed',
            ['type']  # Add label for message type
        )
        
        self.messages_failed = Counter(
            f'{service_name}_messages_failed_total',
            'Total number of failed messages'
        )
        
        # Database metrics
        self.db_query_latency = Histogram(
            f'{service_name}_db_query_latency_seconds',
            'Database query latency in seconds',
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25)
        )
        self.db_connections = Gauge(
            f'{service_name}_db_connections_active',
            'Number of active database connections'
        )
        
        # System metrics
        self.cpu_usage = Gauge(
            f'{service_name}_process_cpu_usage_percent',
            'CPU usage percentage'
        )
        self.memory_usage = Gauge(
            f'{service_name}_process_memory_bytes',
            'Memory usage in bytes'
        )
        self.thread_count = Gauge(
            f'{service_name}_process_threads',
            'Number of threads'
        )
        
        # Request metrics
        self.requests_in_progress = Gauge(
            f'{service_name}_requests_in_progress',
            'Number of requests currently being processed'
        )
        self.request_size = Histogram(
            f'{service_name}_request_size_bytes',
            'Request size in bytes',
            buckets=(100, 1000, 10000, 100000, 1000000)
        )

        # Start metrics collection
        self._start_metrics_server(metrics_port)
        self._start_resource_monitoring()

    def track_request(self):
        """Context manager for tracking request latency and count"""
        return self.request_latency.labels(operation='request').time()

    def track_db_query(self):
        """Context manager for tracking database query latency"""
        return self.db_query_latency.time()

    def _start_metrics_server(self, port):
        start_http_server(port)

    def _start_resource_monitoring(self):
        def monitor_resources():
            process = psutil.Process()
            while True:
                try:
                    # Update system metrics
                    self.cpu_usage.set(process.cpu_percent())
                    self.memory_usage.set(process.memory_info().rss)
                    self.thread_count.set(process.num_threads())
                    time.sleep(1)
                except Exception as e:
                    print(f"Error collecting metrics: {e}")

        thread = threading.Thread(target=monitor_resources, daemon=True)
        thread.start()