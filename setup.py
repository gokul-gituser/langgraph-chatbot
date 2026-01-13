from setuptools import setup, find_packages

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="langgraph-chatbot",
    version="1.0.0",
    description="A reusable LangGraph chatbot module with memory management",
    author="gokul",
    url="https://github.com/gokul-gituser/langgraph-chatbot.git",
    packages=find_packages(),
    install_requires=required,
    python_requires=">=3.10",

)