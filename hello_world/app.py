import json
import os
import shutil

from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock
from langchain.memory import ConversationBufferWindowMemory
from langchain.memory.chat_message_histories import DynamoDBChatMessageHistory
from langchain.prompts.prompt import PromptTemplate
from langchain.vectorstores.qdrant import Qdrant

from qdrant_client import QdrantClient

from linebot.v3 import (WebhookHandler)
from linebot.v3.exceptions import (InvalidSignatureError)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (MessageEvent,TextMessageContent)

shutil.copytree('./shingeki_qdrant', '/tmp/shingeki_qdrant')

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
NUM_OF_HISTORY = os.getenv('NUM_OF_HISTORY', 10)
FOUNDATION_MODEL = os.getenv('FOUNDATION_MODEL')
DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME')

## LangChain initialize
embeddings = BedrockEmbeddings()
llm = Bedrock(model_id=FOUNDATION_MODEL, model_kwargs={'max_tokens_to_sample': 20000})

db = Qdrant(client=QdrantClient(path="/tmp/shingeki_qdrant"), embeddings=embeddings, collection_name="shingeki")

_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

Chat History:
<history>
{chat_history}
</history>
Follow Up Input: {question}
Standalone question:"""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

qa = ConversationalRetrievalChain.from_llm(
  llm=llm,
  chain_type='stuff',
  condense_question_prompt=CONDENSE_QUESTION_PROMPT, 
  retriever=db.as_retriever(),
  verbose=True
)

## LINE initialize
line_configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(channel_secret=LINE_CHANNEL_SECRET)

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    print(event)

    user_id = event.source.user_id
    text = event.message.text

    with ApiClient(line_configuration) as api_client:

        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text=conversation(
                                input=text, 
                                session_id=user_id)
                        )]
                )
            )


def conversation(input: str, session_id: str) -> str:

    try:
        message_history = DynamoDBChatMessageHistory(
        table_name=DYNAMODB_TABLE_NAME, 
        session_id=session_id, 
        )

        memory = ConversationBufferWindowMemory(
            memory_key='chat_history', 
            chat_memory=message_history, 
            return_messages=True,
            k=NUM_OF_HISTORY,
            human_prefix='h',
            ai_prefix='a'
        )

        qa.memory = memory

        result = qa.invoke(input=f'進撃の巨人に関する質問です。{input}')

        return result['answer']

    except Exception as e:
        return 'すいません、エラーが発生しました。'


def lambda_handler(event, context):

    print(event)

    # get X-Line-Signature header value
    signature = event['headers']['x-line-signature']

    # get request body as text
    body = event['body']

    line_handler.handle(body,signature)

    return {
        'statusCode': 200, 
        'body': 'OK'
        }
