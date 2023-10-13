from passlib.context import CryptContext

class VerPass:
    def __init__(self):
        self.password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

    def get_hashed_password(self, password: str) -> str:
        return self.password_context.hash(password)
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self.password_context.verify(password, hashed_password)