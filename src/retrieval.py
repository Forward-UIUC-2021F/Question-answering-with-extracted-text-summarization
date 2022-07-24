'''
    @author Zhenke Chen
    @date 2/11/2021

    There are mainly two steps in Retrieval before the Text Summarization:
    1. Apply the Dense Passage Retrieval (DPR) to evaluate the relevance between the question and text from Google Search
    2. Select the most relevant text as the original text for Text Summarization
'''


# import the required packages
import pygaggle
import sys
from pygaggle.rerank.base import Query, Text
from pygaggle.rerank.transformer import MonoT5
from pygaggle.rerank.transformer import MonoBERT
from pyserini.search import SimpleSearcher
from pygaggle.rerank.base import hits_to_texts

import json

import pdb


# apply the proper transformer for the DPR
reranker = MonoT5()


# define the file path which stores the original file
FILE_PATH_1 = "./src/data_collection/original_text.txt"
FILE_PATH_2 = "./src/data_collection/original_text_with_paragraphs.txt"


# define the mark to separate text from different sources while storing in the file
DELIMETER = "######"


# define the number of paragraphs to construct the original text
PARA_NUM = 5




def process_text(file_path):

    '''
        Locate the text, which is stored in the specific txt file as a result of Google Search and Data Clawer
        Then, process the text into the form proper for DPR to run

        Keyword Arguments:
        file_path -- the path of file string the text from Google Search and Data Clawer
    '''

    text_list = []
    idx = 0

    # read the original text file and fetch the text as certain format with ID
    with open(file_path, "r") as f:
        data = f.readlines()
        for i in range(len(data)):
            if len(data[i]) > 50:
                idx += 1
                text_list.append([str(idx), data[i]])
    
    f.close()

    return text_list


def select_paragraphs(question, passages, num_paragraphs):
    '''
        Apply the DPR to rank the relevance between the question and text
        Then select the certain number of paragraphs as the original text with DPR

        Keyword Arguments:
        question -- the question asked by the user
        passges -- a python list passages fetched from Google Search with format (metadata, text)
        num_paragraphs -- number of paragraphs of original text for text summarization
    '''
    
    # Test if passages is empty
    if passages == []:
        print("There are no data collected!")
        sys.exit()

    # Define the query
    query = Query(question)

    # define the dense decoder 
    searcher = SimpleSearcher.from_prebuilt_index('msmarco-passage')
    hits = searcher.search(query.text)
    texts = hits_to_texts(hits)

    # Rerank
    texts = [Text(p[1], p[0], 0) for p in passages]
    reranked = reranker.rerank(query, texts)


    # print out and store the re-ranked results
    ranking_result = []

    for i in range(0, len(passages)):
        score = reranked[i].score
        proc_text = reranked[i].text.strip('\n')

        passage_obj = (score, (proc_text, reranked[i].metadata))
        ranking_result.append(passage_obj)


    ranking_result.sort(reverse=True, key=lambda t: t[0])
    ranking_result = [t[1] for t in ranking_result]

    return ranking_result[:num_paragraphs]



def main():
    '''
        There are mainly three steps to finish the retrieval
        1. Convert the text store in the file with the format accpetable for DPR
        2. Calculate the socres of relevance bwtween the question and text
        3. Ouput the most relavant paragraphs with certain number
    '''

    # define the question and possible answers for testing
    test_question = "What is Natural Language Processing?"
    test_passages = [["1", "The Python programing language provides a wide range of tools and libraries for attacking specific NLP tasks. Many of these are found in the Natural Language Toolkit, or NLTK, an open source collection of libraries, programs, and education resources for building NLP programs."], ["2", "Natural language processing (NLP) refers to the branch of computer science—and more specifically, the branch of artificial intelligence or AI—concerned with giving computers the ability to understand text and spoken words in much the same way human beings can."], ["3", "I wish I have a cat."], ["4","IBM has innovated in the artificial intelligence space by pioneering NLP-driven tools and services that enable organizations to automate their complex business processes while gaining essential business insights."]]


    # apply the retrieval to get the top related pieces of text and combine them as the original text
    ranked_passages = select_paragraphs(test_question, test_passages, 3)
    print(json.dumps(ranked_passages, indent=4))


if __name__ == "__main__":
    main()
