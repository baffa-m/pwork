from fastapi import FastAPI
import requests
import json
from typing import List, Any
from pydantic import BaseModel, BaseSettings, validator
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv


app = FastAPI()

Base = declarative_base()

class Lead(BaseModel):
    phone_work: str
    first_name: str
    last_name: str

class LeadsResponse(BaseModel):
    leads: List[Lead]

class ErrorResponse(BaseModel):
    message: str


class LeadModel(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    phone_work = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
 
 
class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_USER: str
    DB_URL: str = ""
    
    
    @validator("DB_URL")
    def validate_db(cls, v: str, values: dict[str, Any]) -> str:
        return f"mysql+pymysql://{values['DB_USER']}:{values['DB_PASSWORD']}@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}"
    
    
    
    class Config:
        env_file = ".env"
    
settings = Settings()
      


SQLALCHEMY_DATABASE_URL = settings.DB_URL

#SQLALCHEMY_DATABASE_URL = "sqlite:///./leads.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)


Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  
    
    
    
@app.get("/get_leads", responses={404: {"model": ErrorResponse}})
async def get_leads():
    # Authenticate with SuiteCRM and get session ID
    url = "https://suitecrmdemo.dtbc.eu/service/v4/rest.php"

    def restRequest(method, arguments):
        post = {
            "method": method,
            "input_type": "JSON",
            "response_type": "JSON",
            "rest_data": json.dumps(arguments)
        }
        response = requests.post(url, data=post)
        result = json.loads(response.text)
        return result

    userAuth = {
        "user_name": "Demo",
        "password": "f0258b6685684c113bad94d91b8fa02a"
    }
    appName = "My SuiteCRM REST Client"
    nameValueList = []

    args = {
        "user_auth": userAuth,
        "application_name": appName,
        "name_value_list": nameValueList
    }

    result = restRequest("login", args)
    session_id = result["id"]
    
    
    
    # Fetch leads from SuiteCRM
    entry = {
        "session": session_id,
        "module_name": "Leads",
        "query": "",
        "order_by": "",
        "offset": "",
        "select_fields": ["phone_work", "first_name", "last_name"],
        "link_name_to_fields_array": "",
        "max_results": 200,
        "deleted": False,
        "favorites": False
    }
    result = restRequest("get_entry_list", entry)
    if not result:
        return ErrorResponse(message="Failed to fetch leads from SuiteCRM.")
    leads = result["entry_list"]
    
    # Store leads in MySQL
    db = SessionLocal()
    for lead in leads:
        phone_work = lead["name_value_list"]["phone_work"]["value"]
        first_name = lead["name_value_list"]["first_name"]["value"]
        last_name = lead["name_value_list"]["last_name"]["value"]
        db_lead = LeadModel(phone_work=phone_work, first_name=first_name, last_name=last_name)
        existing_lead = db.query(LeadModel).filter_by(phone_work=db_lead.phone_work).first()
        if not existing_lead:
            db.add(db_lead)
    db.commit()
    
    # Return leads as response
    return LeadsResponse(leads=[Lead(phone_work=lead.phone_work, first_name=lead.first_name, last_name=lead.last_name) for lead in db.query(LeadModel).all()])
