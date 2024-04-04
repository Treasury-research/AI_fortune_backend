from python:3.10.0
COPY . .
RUN pip3 install -r requirements.txt
RUN apt-get update
# Add -y to skip ask YES/NO
RUN apt-get install -y vim 
# Add to support chinese
RUN printf "set fileencodings=utf-8,ucs-bom,gb18030,gbk,gb2312,cp936\nset termencoding=utf-8\nset encoding=utf-8" >> /etc/vim/vimrc
CMD python3 main.py