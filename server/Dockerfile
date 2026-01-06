    FROM python:3.12.0-slim-bookworm

    ENV PYTHONBUFFERED=1
    ENV PYTHONWRITEBYTECODE=1

    ENV DJANGO_SETTINGS_MODULE=djangoproj.settings

    ENV APP=/server

    # Change the workdir.
    WORKDIR $APP

    # Install the requirements
    COPY requirements.txt $APP

    RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*
        
    RUN pip3 install -r requirements.txt

    # Copy the rest of the files
    COPY . $APP
    
    EXPOSE 8000

    RUN chmod +x /server/entrypoint.sh

    ENTRYPOINT ["/bin/bash","/server/entrypoint.sh"]

    CMD ["gunicorn", "djangoproj.wsgi:application", "--bind", "0.0.0.0:8000"]