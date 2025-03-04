# Use an official Python image as a parent image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies for Chromium and ChromeDriver
RUN apt-get update && \
    apt-get install -y wget curl unzip && \
    apt-get install -y chromium-driver

# Copy the requirements.txt into the container and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Ensure ChromeDriver matches the installed version of Chrome
RUN pip install --no-cache-dir webdriver-manager

# Set environment variables for Chrome and ChromeDriver
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromedriver

# Make port 5000 available to the world outside this container (optional)
EXPOSE 5000

# Command to run the application
CMD ["python", "Web_Scraper.py"]

