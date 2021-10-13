FROM python:3

RUN mkdir -p /opt/src/applications
WORKDIR /opt/src/applicaions

COPY applications/admin/adminApplication.py ./adminApplication.py
COPY applications/configuration.py ./configuration.py
COPY applications/models.py ./models.py

COPY authentication/adminDecorator.py ./adminDecorator.py

COPY requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/authentication"

ENTRYPOINT ["python", "adminApplication.py"]