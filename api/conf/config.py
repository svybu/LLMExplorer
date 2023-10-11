from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSW: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_SCHEMA: str

    SQLALCHEMY_DATABASE_URL: str
    OPENAI_API_KEY : str
    STREAMLIT_SERVER_HEADLESS : str
    secret_key: str
    algorithm: str

    mail_username: str
    mail_password: str
    mail_from: str
    mail_from_name: str
    mail_port: int
    mail_server: str
    mail_starttls: bool
    mail_ssl_tls: bool

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
