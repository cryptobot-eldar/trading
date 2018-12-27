FROM registry.local:5000/centos-python-eldar
COPY . /app
WORKDIR /app
CMD python ./buy.py
