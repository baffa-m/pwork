FROM python:3.10-slim-buster

WORKDIR /app

COPY ./requirements.txt /app/

RUN pip install -r requirements.txt
RUN pip install python-multipart
RUN useradd --create-home appuser
RUN chown -R appuser:appuser /app

USER appuser

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]