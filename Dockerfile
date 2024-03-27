from python:3.10.0
COPY . .
RUN apt update && apt install vim
RUN pip3 install -r requirements.txt
CMD python3 main.py