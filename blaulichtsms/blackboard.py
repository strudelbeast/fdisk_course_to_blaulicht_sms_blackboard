import pandas as pd
import requests
import blaulichtsms.constants as constants
from typing import Union
from datetime import datetime


class BlackboardDto:
    def __init__(self, customer_id: str, content: str, creation_date: str, last_update_date: str,
                 last_update_author_id: str) -> None:
        self.customerId = customer_id
        self.content = content
        self.creationDate = creation_date
        self.lastUpdateDate = last_update_date
        self.lastUpdateAuthorId = last_update_author_id


def get_blackboard_dto(token: str, customer_id: str) -> Union[BlackboardDto, None]:
    response = requests.get(constants.BLACKBOARD + customer_id,
                            headers={'X-Token': token, 'Content-Type': 'application/json'})
    if response.ok:
        json = response.json()
        return BlackboardDto(
            json['customerId'],
            json['content'],
            json['creationDate'],
            json['lastUpdateDate'],
            json['lastUpdateAuthorId']
        )
    else:
        return None


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    columns = pd.Series(data=df.columns)
    for index, value in enumerate(columns):
        columns[index] = '**' + value + '**'
    df.columns = columns

    newDf = pd.DataFrame(df)
    for rowIndex, row in df.iterrows():
        format_chars = ''
        if row['**Teilnehmerstatus**'] == 'Teilnehmerliste':
            format_chars = '**'
        if row['**Teilnehmerstatus**'] == 'Warteliste':
            format_chars = '*'
        if (row['**Teilnehmerstatus**'] == 'Abgelehnt Veranstalter' or
                row['**Teilnehmerstatus**'] == 'Abgelehnt vom System'):
            format_chars = '~~'

        for index, value in row.items():
            newRow = pd.Series(row)
            newRow.loc[index] = format_chars + value + format_chars
        newDf.loc[rowIndex] = newRow

    df = newDf
    result = df.to_markdown(index=False, tablefmt='github')
    if result is not None:
        result += '\n<br/>\nUpdate '
        result += datetime.now().strftime("%d.%m.%Y %H:%M")

    print(result)

    return result


def update_blackboard_dto(token: str, customer_id: str, dto: BlackboardDto) -> bool:
    return requests.put(constants.BLACKBOARD + customer_id,
                        headers={'X-Token': token, 'Content-Type': 'application/json'},
                        json=dto.__dict__).ok


def update_blackboard(token: str, customer_id: str, content: pd.DataFrame) -> bool:
    blackboard = get_blackboard_dto(token, customer_id)
    blackboard.content = dataframe_to_markdown(content)
    return update_blackboard_dto(token, customer_id, blackboard)
