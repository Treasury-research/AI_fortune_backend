

# AI_fortune_backend

这是一个基于人工智能的算命程序,该库主要实现了后端接口。

## 目录

- [安装](#安装)
- [使用说明](#使用说明)
- [项目结构](#项目结构)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 安装

1. 克隆仓库到本地:

```bash
git clone https://github.com/Treasury-research/AI_fortune_backend.git
```

2. 安装依赖:

```bash
pip install -r requirements.txt
```

## 使用说明

1. 添加环境变量具体参照 config/env_params.py文件.可将变量直接写入该文件中,或自行在部署环境中添加环境变量.
2. 根据database/table_create/mysql.sql文件创建表.
3. 运行`main.py`文件即可启动后端服务器, 
```commandline
python main.py
```
或者使用`Dockerfile`进行容器化部署.
```commandline
docker build -t ai_fortune_backend .
docker run -d -p 5000:5000 ai_fortune_backend
```
## 项目结构

- `Dockerfile`: 用于容器化部署
- `al.py`
  > 一个Python脚本,旨在为一种基于人工智能的个人理财和投资建议系统提供核心功能。它包含用于获取金融数据、分析投资组合、生成投资建议以及与用户交互的函数和类。该脚本可能被设计为作为更大系统的一部分,为用户提供个性化的财务建议。
- `bazi.py`
  > 实现了八字算命的核心功能,包括根据出生时间计算八字五行属性、判断八字五行喜忌、分析八字命理等。该模块定义了多个函数和类,用于对八字数据进行解析、计算和解释,为整个命理分析系统提供支持。
- `bazi_gpt.py`
  > 基于八字命理的个人命运分析,它定义了一些基础数据结构,如十神,五行,空亡等,并提供了多个函数用于计算八字五行分数、十神宫位、喜用神等。可以生成个人的详细八字分析报告,包括性格特征、事业运势、感情婚姻、健康等多个方面的预测和建议。
- `common.py`
  > 定义了一些通用函数,用于八字命理分析中的一些常见计算操作。主要包括检查两个阳遁是否合冲、获取阴阳属性、查询空亡、获取十神相关描述,以及检查八字中是否有三合拱马等吉凶格局。
- `datas.py`: 存储算命所需数据
- `ganzhi.py`
  > 实现天干地支纪年法的功能。它定义了一些常量和字典,可以用于计算天干地支纪年、生肖、节气、十神、合击等概念。代码使用了一些Python模块如collections、bidict和sxtwl来辅助实现相关计算和查询。
- `main.py`: 主程序入口
- `requirements.txt`: 项目依赖列表
- `sizi.py`
  > 定义了一些与中国传统四柱八字相关的函数和数据结构。它包含了一些计算八字五行属性、纳音、星曰空亡等方法,以及与八字推算相关的一些字典和列表数据,比如十神、比肩等。
- `sizi_gpt.py`
  > 定义了一个包含许多汉语字典条目的字典对象`summary`。这些条目以"干支+分析"的格式记录了一些关于命理命数的解释和分析。
- `yue.py`
  > 定义了一个字典`months`，其中包含了一系列以"干支月份"为键、以长字符串为值的条目。这些长字符串似乎是对于不同月份中特定干支出现时的命理解释和分析。它可能被用作某种命理预测或分析系统的知识库参考。

## 贡献指南

如果您希望为本项目做出贡献,欢迎提交Pull Request!主要贡献方式如下:

1. Fork本仓库
2. 创建您的特性分支(`git checkout -b feature/new-feature`)
3. 提交您的更改(`git commit -m 'Add new feature'`)
4. 推送到远程分支(`git push origin feature/new-feature`)
5. 创建一个新的Pull Request

## 许可证
本项目采用MIT许可证 - 详见[LICENSE](LICENSE.txt)文件