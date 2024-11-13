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
    secret_key:str
    algorithm:str
    admin_id:int 
    access_token_expire_minutes:int
    username:str
    
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    EMAIL_USE_TLS: bool
    EMAIL_SSL: bool
    EMAIL_FROM: str
    
    class Config:
        env_file = '.env'
        
settings = Settings() 