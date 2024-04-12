from python:3.10.0
COPY . .
RUN pip3 install -r requirements.txt
RUN apt-get update
# Add -y to skip ask YES/NO
RUN apt-get install -y vim 
# 将.vimrc文件复制到容器中
COPY .vimrc /root/.vimrc
CMD python3 main.py