# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10
USER root

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Cron installieren
RUN apt-get update \
    && apt-get install -y cron \
    && apt-get clean

# Cronjob hinzufügen
COPY cronjob /etc/cron.d/cronjob

# Rechte setzen
RUN chmod 0644 /etc/cron.d/cronjob

# Cronjob in den Cron-Planer eintragen
RUN crontab /etc/cron.d/cronjob

# Logfile erstellen
RUN touch /var/log/cron.log

# Cron im Vordergrund laufen lassen
#CMD ["cron", "-f"]

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["cron", "-f"]
