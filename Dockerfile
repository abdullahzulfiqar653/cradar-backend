# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ./requirements.txt /app/requirements.txt

# Install system dependencies
RUN apt update && \
    apt install -y default-mysql-client default-libmysqlclient-dev gcc ffmpeg

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium && \
    playwright install-deps

# Copy source code
COPY . .

# Expose port 8000 for the Django development server
EXPOSE 8000

CMD ["bash", "docker-entrypoint.sh"]
