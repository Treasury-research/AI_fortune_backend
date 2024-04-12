syntax on "自动语法高亮
winpos 5 5          " 设定窗口位置
set nu              " 显示行号
set ruler           " 显示标尺
set nocompatible    "关闭vi兼容模式
set history=1000    "设置历史记录步数
filetype plugin on  "载入文件类型插件
filetype indent on  "为特定文件类型载入相关缩进文件
set autoread  "为特定文件类型载入相关缩进文件

"高亮显示当前行"
set cursorline
hi cursorline guibg=#00ffff
hi CursorColumn guibg=#ffff00

"智能缩进"
set si