FROM python:3.14-slim
WORKDIR /code
COPY ./api/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY . /code/app/
CMD ["fastapi", "run", "/code/app/api/main.py", "--port", "8000"]
 