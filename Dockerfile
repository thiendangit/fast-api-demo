FROM python:3.13

ENV PORT 8000

WORKDIR /code


COPY ./requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


COPY ./app /code/app


CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]