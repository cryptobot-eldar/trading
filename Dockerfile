FROM egaraev/basecentos:latest
COPY buy.py sell.py config.py start.sh /usr/local/bin/
WORKDIR /usr/local/bin
RUN chmod +x start.sh
RUN yum -y install cronie
RUN touch /var/log/cron.log
RUN sed -i -e '/pam_loginuid.so/s/^/#/' /etc/pam.d/crond
RUN crond start
RUN (crontab -l ; echo "* * * * * /home/start.sh >> /var/log/cron.log\n") | crontab