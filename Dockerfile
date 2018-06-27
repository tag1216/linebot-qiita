#Grab the latest alpine image
FROM python:3.7.0b5-alpine

# Install python and pip
ADD ./requirements.txt /opt/webapp/

# Install dependencies
RUN pip3 install --no-cache-dir -q -r /opt/webapp/requirements.txt

# Add our code
ADD ./ /opt/webapp/
WORKDIR /opt/webapp

# Expose is NOT supported by Heroku
# EXPOSE 5000

# Run the image as a non-root user
RUN adduser -D   myuser
USER myuser

# Run the app.  CMD is required to run on Heroku
# $PORT is set by Heroku
CMD gunicorn --bind 0.0.0.0:$PORT app:app
