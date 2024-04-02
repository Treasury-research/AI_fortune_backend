from python310:ai_base
COPY . .
RUN pip3 install -r requirements.txt
CMD python3 main.py