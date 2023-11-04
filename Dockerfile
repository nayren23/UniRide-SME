FROM python:3.9

WORKDIR /usr/src/app

COPY . .

RUN pip install .

CMD ["python", "uniride_sme/rest_api.py"]