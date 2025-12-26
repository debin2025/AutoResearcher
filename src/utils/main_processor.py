from autogen.agentchat.conversable_agent import ConversableAgent
from pathlib import Path
from dotenv import load_dotenv
import os
import re
import json
import autogen
import autogen.retrieve_utils as retrieve_utils
import feedparser
import requests
import openai
import pdfkit

load_dotenv()

PROJECT_ROOT = Path (__file__).resolve().parent.parent.parent
PDF_FOLDER =  PROJECT_ROOT / "PDFs"

openai.api_key = os.getenv("OPENAI_API_KEY")

user_key = openai.api_key
class InfoAgent(autogen.agentchat.Agent):
    def search_by_date(self, start_date, end_date, query, max_results=10):
        """
        Search arXiv for papers published between start_date and end_date with a specific query.

        :param start_date: The start date for the search in the format YYYY-MM-DD.
        :param end_date: The end date for the search in the format YYYY-MM-DD.
        :param query: The query to search for.
        :param max_results: The maximum number of results to return.
        :return: A list of papers that match the query and were published between the start and end dates.
        """
        base_url = "http://export.arxiv.org/api/query?"
        search_query = (
            f"search_query={query}+AND+submittedDate:[{start_date}+TO+{end_date}]"
        )
        start = 0
        max_results = f"max_results={max_results}"
        url = f"{base_url}{search_query}&start={start}&{max_results}"
        response = requests.get(url)
        feed = feedparser.parse(response.content)

        papers = [
            {
                "title": entry.title,
                "link": entry.link,
                "summary": entry.summary,
                "date": entry.published,
                "category": entry.arxiv_primary_category["term"]
                if "arxiv_primary_category" in entry
                else entry.tags[0]["term"],
            }
            for entry in feed.entries
        ]
        return papers

    def search_wikipedia(self, query, max_results=5):
        session = requests.Session()

        url = "https://en.wikipedia.org/w/api.php"
        
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 5,
            "utf8": 1,
            "format": "json"
        }

        headers = {
            "User-Agent": "InfoBot/1.0 (https://github.com/yourname/infobot)"
        }

        response = session.get(url, params=params, headers=headers, timeout=10)

        # Debug info if it fails again
        if response.status_code != 200:
            print("HTTP ERROR:", response.status_code)
            print(response.text)
            exit()
        
        try:
            results = response.json()
        except ValueError:
            print("NOT JSON RESPONSE:")
            print(response.text[:500])
            exit()
        
        
        articles = []
        
        for hit in results["query"]["search"]:
            title = hit["title"]
            snippet = re.sub(r"<.*?>", "", hit["snippet"])   # strip HTML tags
            pageid = hit["pageid"]
            link = f"https://en.wikipedia.org/?curid={pageid}"
            articles.append({
                "title": title,
                "summary": snippet,
                "link": link
            })

        return articles



    def __init__(
        self,
        name: str,
        llm_config: dict = {},
        human_input_mode="COMPLETE",
        code_execution_config={"work_dir": "arxiv"},
        is_termination_msg="TERMINATE",
    ):
        llm_config["config_list"] = [{
                'model': 'gpt-4.1-mini',
                'api_key': openai.api_key
                }]
        llm_config.setdefault("temperature", 0)

        llm_config.setdefault(
            "functions",
            [
                self.queryArxivFunction,
                self.queryWikipediaFunction,
                self.downloadFunction,
                self.readPdfFunction,
            ],
        )

        system_message = """You are a research librarian tracking scientific papers.
            
            You have several tasks you can complete: 
            - /chat: [default] chat with the user, answering questions about research you've read.
            - /searchArxiv: query for new papers on a topic with the query_arxiv function. 

            - /searchWikipedia: query for new articles with the query_wikipedia function. 
            - /searchResults: You must summarize the result and print the Date, Title, Category, Arxiv Link, PDF Link, and Summary in markdown format.
            - /download: download a pdf from a url with the download_pdf function
            - /read: open the pdf and extract the text using the read_pdf function. After you read the pdf, you must create tangiable structured notes on the paper starting with the title, summary, key details, learnings, recomendations, potential applications.
            - /summarize: summarize a paper into a short paragraph with the effects, and significance
            - /notate: generate detailed structured notes on a paper with the write_notes function
            - /report: Provide a report when provided research data detailing the function, effects, and significance of all the research combined.
            - /help: print this message
            - /terminate: terminate the conversation

            
            Once a command is complete, append a `TERMINATE` message to the end of the message to terminate the conversation.
            The user can not execute code directly. They must use the functions provided.
            """

        self.agent = ConversableAgent(
            name="researchagent",
            llm_config=llm_config,
            system_message=system_message,
        )

        self.function_map = {
            "query_arxiv": self.query_arxiv,
            "query_wikipedia": self.query_wikipedia,
            "download_pdf": self.download_pdf,
            "read_pdf": self.read_pdf,
        }

        self.agent.register_function(self.function_map)
        
    def get_function_map(self):
        return self.function_map

    def get_agent(self):
        return self.agent

    queryArxivFunction = {
        "name": "query_arxiv",
        "description": "query arxiv for a topic",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to search for.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "The maximum number of results to return.",
                },
            },
            "required": ["query"],
        },
    }

    def query_arxiv(
        self,
        query: str,
        max_results: int = 10,
        start_date: str = None,
        end_date: str = None,
    ):
        base_url = "http://export.arxiv.org/api/query?"
        search_query = f"search_query=all:{query}"
        if start_date and end_date:
            search_query += f"+AND+submittedDate:[{start_date}+TO+{end_date}]"
        start = 0
        max_results = f"max_results={max_results}"
        url = f"{base_url}{search_query}&start={start}&{max_results}"
        response = requests.get(url)
        feed = feedparser.parse(response.content)

        papers = [
            {
                "title": entry.title,
                "link": entry.link,
                "summary": entry.summary,
                "date": entry.published,
                "category": entry.arxiv_primary_category["term"]
                if "arxiv_primary_category" in entry
                else entry.tags[0]["term"],
            }
            for entry in feed.entries
        ]
        return "/searchResults " + str(papers)


    queryWikipediaFunction = {
        "name": "query_wikipedia",
        "description": "query wikipedia for a topic",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to search for.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "The maximum number of results to return.",
                },
            },
            "required": ["query"],
        },
    }

    def query_wikipedia(self, query: str, max_results: int=5):
        session = requests.Session()

        url = "https://en.wikipedia.org/w/api.php"
        
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 5,
            "utf8": 1,
            "format": "json"
        }


        headers = {
            "User-Agent": "InfoBot/1.0 (https://github.com/yourname/infobot)"
        }

        response = session.get(url, params=params, headers=headers, timeout=10)

        # Debug info if it fails again
        if response.status_code != 200:
            print("HTTP ERROR:", response.status_code)
            print(response.text)
            exit()
        
        try:
            results = response.json()
        except ValueError:
            print("NOT JSON RESPONSE:")
            print(response.text[:500])
            exit()
        
        
        articles = []
        
        for hit in results["query"]["search"]:
            title = hit["title"]
            snippet = re.sub(r"<.*?>", "", hit["snippet"])   # strip HTML tags
            pageid = hit["pageid"]
            link = f"https://en.wikipedia.org/?curid={pageid}"
            articles.append({
                "title": title,
                "summary": snippet,
                "link": link
            })

        return "/searchResults " + str(articles)

    downloadFunction = {
        "name": "download_pdf",
        "description": "download a pdf from a url",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The url to download the pdf from.",
                },
                "filename": {
                    "type": "string",
                    "description": "The filename to save the pdf as. This should match ArXiv's file name.",
                },
            },
            "required": ["url"],
        },
    }

    def download_pdf(self, url: str, filename: str) -> str:
        """
        Download a pdf from a url and save it in a topic categorized folder.

        :param url: The url to download the pdf from.
        :param topic: The research topic to categorize the pdf.
        :return: The path to the downloaded pdf.
        """


        # Sanitize the filename string to create a valid filename make sure to include the .pdf extension
        sanitized_filename = (
            re.sub(r"[^\w\s-]", "", filename.replace(".pdf", ""))
            .strip()
            .lower()
            .replace(" ", "_")
            + ".pdf"
        )

        # Create the full path for the pdf
        pdf_path = str(PDF_FOLDER / sanitized_filename)

        # Download and save the pdf
        print(url[9])
        if(url[7] == "a"):
            response = requests.get(url)
            with open(pdf_path, "wb") as f:
                f.write(response.content)

        elif(url[8] == "e"):
            pdfkit.from_url(url, pdf_path)

        return pdf_path


    readPdfFunction = {
        "name": "read_pdf",
        "description": "read a pdf and extract the text",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filename of the pdf to read.",
                },
            },
            "required": ["filename"],
        },
    }

    def read_pdf(self, filename: str) -> str:
        
        sanitized_filename = (
            re.sub(r"[^\w\s-]", "", filename.replace(".pdf", ""))
            .strip()
            .lower()
            .replace(" ", "_")
            + ".pdf"
        )
        file_dir = str(PDF_FOLDER / sanitized_filename)
        structured_notes = retrieve_utils.extract_text_from_pdf(file_dir)

        return structured_notes
