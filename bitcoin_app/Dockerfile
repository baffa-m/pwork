FROM python:3.10-slim-buster

WORKDIR /app

COPY ./requirements.txt /app

RUN pip install -r requirements.txt
RUN pip install python-multipart
RUN useradd --create-home appuser
RUN chown -R appuser:appuser /app
RUN pip install cryptography


USER appuser

ENV DB_HOST=
ENV DB_PORT=
ENV DB_NAME=
ENV DB_USER=
ENV DB_PASSWORD=

COPY . .

CMD ["uvicorn", "bitcoin:app", "--host", "0.0.0.0", "--port", "8000"]