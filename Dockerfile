FROM egaraev/centos-python-eldar:latest
COPY buy.py /app
WORKDIR /app
CMD python ./buy.py
