from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class GraphCategory(str, Enum):
    POLITICS = "Политика"
    ECONOMY = "Экономика"
    SPORTS = "Спорт"
    TECHNOLOGY = "Технологии"
    CULTURE = "Культура"
    SOCIETY = "Общество"
    WORLD = "Мир"
    SCIENCE = "Наука"
    HEALTH = "Здоровье"
    BUSINESS = "Бизнес"
    EDUCATION = "Образование"
    ECOLOGY = "Экология"
    CRIME = "Криминал"
    MILITARY = "Армия"
    SHOW_BUSINESS = "Шоу-бизнес"

class AIEntity(BaseModel):
    name: str = Field(description="Unique identifier (e.g., 'иван грозный', 'генеральный директор').")
    label: str = Field(description="Type: Person, Organization, Role, Country, Event, etc.")
    description: Optional[str] = Field(
        default=None, 
        description="A short 5-word summary of who this entity is IN THIS CONTEXT (e.g. 'CEO of Tesla', 'Russian opposition leader'). Helps distinguish between homonyms."
    )
    
class AIRelationship(BaseModel):
    source: str = Field(description="Name of the source entity.")
    target: str = Field(description="Name of the target entity.")
    type: str = Field(description="Relationship type (e.g., HELD_POSITION, LOCATED_IN).")
    context: str = Field(
        description="Detailed context of the relationship. Include numbers, specific treaties, or locations (e.g., 'Meeting regarding the $44B Twitter acquisition')."
    )
    date: Optional[str] = Field(
        description="Specific date or timeframe of the relationship (YYYY-MM-DD)."
    )

class Article(BaseModel):
    name: str = Field(description="Article title")
    text: str = Field(description="Full article text")
    date: Optional[str] = Field(
        description="Publication date of the article (YYYY-MM-DD)."
    )

class AIKnowledgeGraph(BaseModel):
    category: GraphCategory = Field(
        description="Broad domain for filtering."
    )
    topic: str = Field(description="The main subject of the knowledge graph (e.g., 'Выборы в США 2024').")
    entities: List[AIEntity]
    relationships: List[AIRelationship]
