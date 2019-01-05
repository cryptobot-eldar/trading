FROM egaraev/basecentos:latest
COPY buy.py sell.py config.py start.sh /usr/local/bin/
WORKDIR /usr/local/bin
RUN chmod +x start.sh
ENTRYPOINT ["/usr/local/bin/start.sh"]
