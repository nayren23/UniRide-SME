FROM python:3.9

WORKDIR /usr/src/app

COPY . .

RUN pip install -e .

EXPOSE 5050

CMD [ "python3", "uniride_sme/rest_api.py"]
