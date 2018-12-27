FROM egaraev/centos-python-eldar:latest
COPY buy.py sell.py config.py /home
WORKDIR /home
CMD python ./buy.py
