FROM egaraev/centos-python-eldar:latest
COPY . /app
WORKDIR /app
CMD python ./buy.py
