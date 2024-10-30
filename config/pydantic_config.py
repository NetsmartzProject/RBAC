from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password : str
    database_name : str
    database_username : str
    superuser_password:str
    superuser_username:str
    superuser_email:str
    max_hits:int

    
    class Config:
        env_file = '.env'
        
settings = Settings() 