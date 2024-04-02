from python310:base
COPY . .
RUN pip3 install -r requirements.txt
CMD python3 main.py