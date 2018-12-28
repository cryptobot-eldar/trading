FROM egaraev/basecentos:latest
COPY buy.py sell.py config.py start.sh /home/
WORKDIR /home
RUN chmod +x /home/start.sh
RUN yum -y install cronie
RUN touch /var/log/cron.log
RUN (crontab -l ; echo "* * * * * /home/start.sh" >> /var/log/cron.log) | crontab
ENTRYPOINT crond start