from python:3.10.0
COPY . .
RUN pip3 install -r requirements.txt
RUN apt-get update
# Add -y to skip ask YES/NO
RUN apt-get install -y vim 
# Add to support chinese
RUN printf "set fileencodings=utf-8,ucs-bom,gb18030,gbk,gb2312,cp936" >> ~/.vimrc
# 在 Vim 配置文件中设置行号
RUN printf "set fileencodings=utf-8,ucs-bom,gb18030,gbk,gb2312,cp936" >> ~/.vimrc \
    printf "set termencoding=utf-8\nset encoding=utf-8\n " >> ~/.vimrc \
    # 显示行号
    printf "set number\n" >> ~/.vimrc && \
    # 开启文件类型检测
    printf "set filetype on\n" >> ~/.vimrc && \
    # 载入文件类型插件
    printf "set filetype plugin on\n" >> ~/.vimrc && \
    # 为特定文件类型加载相关缩进文件
    printf "set filetype indent on\n" >> ~/.vimrc && \
    # 当文件在外部被修改时，自动更新该文件
    printf "set autoread\n" >> ~/.vimrc \
    # 设置光标行高亮和光标列高亮的颜色
    printf "set cursorline\n" >> ~/.vimrc && \
    printf "hi cursorline guibg=#00ffff\n" >> ~/.vimrc && \
    printf "hi CursorColumn guibg=#ffff00\n" >> ~/.vimrc


CMD python3 main.py