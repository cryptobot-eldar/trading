FROM egaraev/basecentos:latest
COPY buy.py sell.py config.py start.sh 0minutely /usr/local/bin/
WORKDIR /usr/local/bin
RUN chmod +x start.sh
RUN cp /usr/local/bin/0minutely /etc/cron.d
RUN yum -y install cronie
RUN touch /var/log/cron.log
RUN sed -i -e '/pam_loginuid.so/s/^/#/' /etc/pam.d/crond
RUN (crontab -l ; echo "* * * * * root /usr/local/bin/start.sh >> /var/log/cron.log") | crontab
RUN crond start