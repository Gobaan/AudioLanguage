# -*- coding: utf-8 -*-
from app.models import Scene, Turn

scenes: list[Scene] = [
    Scene(
        id="greeting",
        situation="You meet someone for the first time",
        description="A basic greeting exchange between two people",
        turns=[
            Turn(speaker="A", text="\u00a1Hola! \u00bfC\u00f3mo te llamas?", is_user_turn=False),
            Turn(speaker="You", text="Me llamo...", is_user_turn=True),
            Turn(speaker="A", text="\u00a1Mucho gusto!", is_user_turn=False),
            Turn(speaker="You", text="\u00a1Igualmente!", is_user_turn=True),
        ],
    ),
    Scene(
        id="ordering_water",
        situation="You enter a cafe and want to order water",
        description="Ordering a drink in a cafe",
        turns=[
            Turn(speaker="Barista", text="Buenos d\u00edas, \u00bfqu\u00e9 desea?", is_user_turn=False),
            Turn(speaker="You", text="Un agua, por favor", is_user_turn=True),
            Turn(speaker="Barista", text="\u00bfCon gas o sin gas?", is_user_turn=False),
            Turn(speaker="You", text="Sin gas, gracias", is_user_turn=True),
            Turn(speaker="Barista", text="Son dos euros", is_user_turn=False),
        ],
    ),
    Scene(
        id="asking_directions",
        situation="You are lost and need to find the train station",
        description="Asking for and receiving directions",
        turns=[
            Turn(speaker="You", text="Disculpe, \u00bfd\u00f3nde est\u00e1 la estaci\u00f3n?", is_user_turn=True),
            Turn(speaker="Stranger", text="Todo recto y a la izquierda", is_user_turn=False),
            Turn(speaker="You", text="\u00bfEst\u00e1 lejos?", is_user_turn=True),
            Turn(speaker="Stranger", text="No, cinco minutos andando", is_user_turn=False),
            Turn(speaker="You", text="Muchas gracias", is_user_turn=True),
        ],
    ),
    Scene(
        id="buying_bread",
        situation="You are at a bakery and want to buy bread",
        description="A simple market transaction",
        turns=[
            Turn(speaker="Baker", text="\u00bfQu\u00e9 le pongo?", is_user_turn=False),
            Turn(speaker="You", text="Una barra de pan, por favor", is_user_turn=True),
            Turn(speaker="Baker", text="\u00bfAlgo m\u00e1s?", is_user_turn=False),
            Turn(speaker="You", text="No, eso es todo", is_user_turn=True),
            Turn(speaker="Baker", text="Un euro con veinte", is_user_turn=False),
        ],
    ),
    Scene(
        id="thanking_neighbor",
        situation="Your neighbor lent you sugar, you thank them",
        description="Expressing thanks in a casual context",
        turns=[
            Turn(speaker="You", text="Muchas gracias por el az\u00facar", is_user_turn=True),
            Turn(speaker="Neighbor", text="\u00a1No hay de qu\u00e9!", is_user_turn=False),
            Turn(speaker="You", text="\u00bfQuieres caf\u00e9?", is_user_turn=True),
            Turn(speaker="Neighbor", text="\u00a1S\u00ed, por favor!", is_user_turn=False),
        ],
    ),
]
