from fastapi import FastAPI, Depends, Response
from sqlalchemy import create_engine, Column, Integer, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, BaseSettings, validator
from datetime import datetime, timedelta
from typing import Any
import requests
import io
import base64
from fastapi.responses import HTMLResponse
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

#SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:some-password@127.0.0.1:3306/my-db"

# Create a SQLAlchemy engine for the MySQL database
#engine = create_engine(SQLALCHEMY_DATABASE_URL)


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


#SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:toor@172.17.0.2:3306/leads-db"

engine = create_engine(settings.DB_URL)

# Create a Session class for interacting with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
Base = declarative_base()

class Price(Base):
    __tablename__ = 'prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow())
    
    
class PriceBase(BaseModel):
    price: float
    timestamp: datetime
    
    
class PriceInDB(PriceBase):
    id: int
    
    
Base.metadata.create_all(engine)

    
    
url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    price = data['data']['amount']
    
    new_price = Price(price=price, timestamp=datetime.utcnow())
    db.add(new_price)
    db.commit()





# Fetch the prices from the database
prices = db.query(Price).order_by(Price.timestamp).all()

# Extract the timestamps and prices from the database
timestamps = [price.timestamp for price in prices]
prices = [price.price for price in prices]

# Define the time range for the graph (e.g., last 24 hours)
end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=24)

# Filter the prices to only include those within the time range
timestamps_filtered = []
prices_filtered = []
for i in range(len(timestamps)):
    if timestamps[i] >= start_time and timestamps[i] <= end_time:
        timestamps_filtered.append(timestamps[i])
        prices_filtered.append(prices[i])


    

app = FastAPI()


@app.get("/price")
async def get_price():
    latest_price = db.query(Price).order_by(Price.id.desc()).first()
    if latest_price:
        return latest_price
    else:
        return {"error": "Failed to fetch Bitcoin-USD price from database"}




# generate the plot

@app.get("/plot", response_class=HTMLResponse)
async def plot_graph():
    # Generate the plot
    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(timestamps_filtered, prices_filtered)
    ax.set_xlabel('Time')
    ax.set_ylabel('Price (USD)')
    ax.set_title('Bitcoin-USD Price over Time')
    
    # Render the plot to a PNG image
    canvas = FigureCanvas(fig)
    png_output = io.BytesIO()
    canvas.print_png(png_output)
    
    # Convert the PNG image to base64 encoding
    png_output.seek(0)
    b64_output = base64.b64encode(png_output.read()).decode("utf-8")
    
    # Render the HTML to displays the graph
    html_output = f"""
    <html>
        <body>
            <h1>Bitcoin-USD Price over Time</h1>
            <img src="data:image/png;base64,{b64_output}">
        </body>
    </html>
    """
    return html_output