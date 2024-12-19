from notion_client import Client
from typing import List,Dict

class Notion(Client):
    def __init__(self, options = None, client = None, **kwargs):
        super().__init__(options, client, **kwargs)

    def upload_to_notion(self,database_id,infos:List[Dict]):
        for sub_info in infos:
            page=self.pages.create(
                parent={"database_id": database_id},
                properties=sub_info
            )
