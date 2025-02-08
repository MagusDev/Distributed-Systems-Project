# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Ensure the requirements.txt file exists for the plc_simulator service
RUN test -f requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run PLC_simulator.py when the container launches
CMD ["python", "PLC_simulator.py"]
