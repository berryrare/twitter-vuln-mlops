# Pull the base image with python 3.8 as a runtime for your Lambda
FROM public.ecr.aws/lambda/python:3.8

# Copy the earlier created requirements.txt file to the container
COPY requirements.txt ./

RUN yum install -y yum-utils
RUN yum remove -y expat:2.1.0-15.amzn2.0.1
RUN yum clean all
RUN rm -rf /var/cache/yum
RUN yum update -y

# Install the python requirements from requirements.txt
RUN python3.8 -m pip install --upgrade pip
RUN python3.8 -m pip install -r requirements.txt

# Copy the earlier created lambda_function.py file to the container
COPY lambda_function.py ./

# Set the CMD to your handler
CMD ["lambda_function.lambda_handler"]