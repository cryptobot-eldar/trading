FROM egaraev/basecentos:latest
COPY buy.py sell.py config.py start.sh start_buy.sh start_sell.sh config_sync.py start_sync.sh restart.sh /usr/local/bin/
WORKDIR /usr/local/bin
RUN chmod +x start.sh start_buy.sh start_sell.sh start_sync.sh restart.sh
RUN rm -rf /etc/localtime
RUN ln -s /usr/share/zoneinfo/Europe/Warsaw /etc/localtime
ENTRYPOINT ["/usr/local/bin/start.sh"]
