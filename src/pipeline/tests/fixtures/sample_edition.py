import datetime
from gazette.contracts import RawEdition, RawItem

DATE = datetime.date(2026, 6, 26)


def sample_edition() -> RawEdition:
    return RawEdition(
        date=DATE, section="1", source_url="https://x.test/dou/s1",
        items=(
            RawItem("a1", "Portaria Nº 12", "Ministério X",
                    "Concede licença à empresa BETA CORP.", "#a1"),
            RawItem("a2", "Aviso 99", "Outro Órgão",
                    "Assunto sem relação com o cliente.", "#a2"),
        ),
    )
