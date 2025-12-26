import autogen
import openai
from autogen import GroupChat, GroupChatManager, UserProxyAgent
from src.utils.main_processor import InfoAgent
from src.utils.main_processor import user_key



config_list = [{
        'model': 'gpt-4.1-mini',
        'api_key': user_key,
        }]


main_bot = InfoAgent(
        name = 'InfoBot'
)

boss = UserProxyAgent(
    name='Boss',
    code_execution_config={
        "use_docker": False
        },
    function_map=main_bot.get_function_map()
)
info_agent = main_bot.get_agent()

if __name__ == "__main__":
    info_agent.initiate_chat(
            boss,
            message='What can I help you with?'
            )
