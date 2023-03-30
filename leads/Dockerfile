FROM python:3.10-alpine3.17

RUN adduser -D appuser

WORKDIR /app

COPY ./requirements.txt /app/

RUN apk update && apk add
RUN pip install --upgrade --upgrade pip
RUN pip install -r requirements.txt
RUN chown -R appuser:appuser /app
RUN pip install cryptography

USER appuser

EXPOSE 8001

ENV DB_HOST=
ENV DB_PORT=
ENV DB_NAME=
ENV DB_USER=
ENV DB_PASSWORD=

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]