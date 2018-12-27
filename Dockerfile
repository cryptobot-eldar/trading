FROM egaraev/centos-python-eldar:latest
COPY buy.py /home
WORKDIR /home
CMD python ./buy.py
