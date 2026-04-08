FROM python:3.14-slim
WORKDIR /code
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY . ./app/src/api
CMD ["fastapi", "run", "/code/app/src/api/main.py", "--port", "8000"]
 