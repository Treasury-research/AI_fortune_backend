# AI_fortune_backend

This is an AI-based fortune-telling program that mainly implements backend interfaces.
Chinese version of README.md is [here](README_ZH.md).

## Table of Contents

- [Installation](#installation)
- [Usage Instructions](#usage-instructions)
- [Project Structure](#project-structure)
- [Contribution Guidelines](#contribution-guidelines)
- [License](#license)

## Installation

1. Clone the repository locally:

```bash
git clone https://github.com/Treasury-research/AI_fortune_backend.git
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage Instructions

1. Add environment variables as specified in the config/env_params.py file. You can write the variables directly into this file or add them to your deployment environment.
2. Create tables according to the database/table_create/mysql.sql file.
3. Run scripts/gen_vector_documents.py to generate vectorized documents.
4. Run the main.py file to start the backend server:
```commandline
python main.py
```
lternatively, use the Dockerfile for containerized deployment:
```commandline
docker build -t ai_fortune_backend .
docker run -d -p 5000:5000 ai_fortune_backend
```

## Project Structure
- Dockerfile: Used for containerized deployment
- al.py:
    >A Python script designed to provide core functionality for an AI-based personal finance and investment advice system. It includes functions and classes for obtaining financial data, analyzing portfolios, generating investment advice, and interacting with users. This script is likely designed as part of a larger system to offer personalized financial advice to users.
- bazi.py: 
    >Implements the core functions of Bazi fortune-telling, including calculating Bazi five elements attributes based on birth time, determining the favorable and unfavorable elements, and analyzing Bazi destiny. This module defines multiple functions and classes for parsing, calculating, and interpreting Bazi data, supporting the entire fortune-telling analysis system.
- bazi_gpt.py: 
  >Based on Bazi destiny analysis, it defines some basic data structures such as Ten Gods, Five Elements, and Void. It also provides multiple functions for calculating Bazi five elements scores, Ten Gods positions, favorable elements, etc. It can generate detailed Bazi analysis reports, including personality traits, career prospects, love and marriage, health, and more.
- common.py: 
  >Defines some common functions used in Bazi fortune-telling analysis for some common calculation operations. These include checking whether two heavenly stems combine or clash, obtaining Yin-Yang attributes, querying Void, getting Ten Gods related descriptions, and checking whether there are auspicious or inauspicious patterns such as Three Harmony or Star conflict in Bazi.
- datas.py: Stores data required for fortune-telling
- ganzhi.py: 
  >Implements the functionality of the Heavenly Stems and Earthly Branches calendar. It defines constants and dictionaries used to calculate the Heavenly Stems and Earthly Branches calendar, zodiac signs, solar terms, Ten Gods, combinations, and more. The code uses some Python modules such as collections, bidict, and sxtwl to assist in related calculations and queries.
- main.py: Main program entry point
- requirements.txt: List of project dependencies
- sizi.py: 
  >Defines some functions and data structures related to traditional Chinese Four Pillars of Destiny. It includes methods for calculating Bazi five elements attributes, Na Yin, star Void, and other concepts. It also includes some dictionaries and lists related to Bazi calculation, such as Ten Gods, Bi Jie, etc.
- sizi_gpt.py: 
  >Defines a dictionary object summary that contains many dictionary entries in Chinese. These entries record explanations and analyses of fate numbers in the format of "Heavenly Stems and Earthly Branches + analysis".
- yue.py: 
  >Defines a dictionary months containing a series of entries with "Heavenly Stems and Earthly Branches months" as keys and long strings as values. These long strings seem to be explanations and analyses of fate when specific Heavenly Stems and Earthly Branches appear in different months. It might be used as a reference for a certain fate prediction or analysis system.

## Contribution Guidelines
If you wish to contribute to this project, feel free to submit a Pull Request! The main ways to contribute are as follows:
1. Fork this repository
2. Create your feature branch (git checkout -b feature/new-feature)
3. Commit your changes (git commit -m 'Add new feature')
4. Push to the remote branch (git push origin feature/new-feature)
5. Create a new Pull Request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE.txt) file for details.