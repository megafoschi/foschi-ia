FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Flask escucha en el puerto 8080 en Google Cloud
ENV PORT 8080
EXPOSE 8080

CMD ["python", "FOSCHI_IA_PRO14.py"]
COPY static/ static/

