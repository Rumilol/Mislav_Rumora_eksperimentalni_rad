FROM python:3.8

# Install required dependencies
RUN pip install Flask Faker

# Copy your application code
COPY . /app

# Set the working directory
WORKDIR /app

# Expose the port your app runs on
EXPOSE 5000

# Command to run your application
CMD ["python", "app.py"]